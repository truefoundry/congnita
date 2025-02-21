import base64
import json
import os
import tempfile
from typing import Any
from urllib.parse import urlparse

from fastapi import Body, HTTPException
from langchain_core.messages import HumanMessage
from pandasai import Agent
from pandasai.connectors import MySQLConnector, PostgreSQLConnector, SqliteConnector

from backend.constants import DataSourceType
from backend.logger import logger
from backend.modules.dataloaders.loader import get_loader_for_data_source
from backend.modules.metadata_store.client import get_client
from backend.modules.model_gateway.model_gateway import model_gateway
from backend.modules.query_controllers.base import BaseQueryController
from backend.modules.query_controllers.structured.payload import (
    CSV_STRUCTURED_PAYLOAD,
    CSV_STRUCTURED_PLOTTING_PAYLOAD,
    DB_STRUCTURED_PAYLOAD,
    DB_STRUCTURED_WHERE_PAYLOAD,
    GSHEET_STRUCTURED_PAYLOAD,
    RESPONSE_REFORMAT_QUERY,
)
from backend.modules.query_controllers.structured.types import StructuredQueryInput
from backend.modules.query_controllers.types import Answer
from backend.server.decorators import post, query_controller
from backend.types import DataIngestionMode

EXAMPLES = {
    "csv": CSV_STRUCTURED_PAYLOAD,
    "csv-plotting": CSV_STRUCTURED_PLOTTING_PAYLOAD,
    "gsheet": GSHEET_STRUCTURED_PAYLOAD,
    "db": DB_STRUCTURED_PAYLOAD,
    "db-where": DB_STRUCTURED_WHERE_PAYLOAD,
}


@query_controller("/structured")
class StructuredQueryController(BaseQueryController):
    """Controller for handling structured data queries using PandasAI"""

    def _detect_source_type(self, uri: str) -> str:
        """Detect the type of structured data source"""
        # For TrueFoundry data directories
        if uri.startswith("data-dir:"):
            return "csv"  # Default to CSV for data-dir

        # For local directories
        if os.path.isdir(uri):
            files = [
                f for f in os.listdir(uri) if f.endswith((".csv", ".xlsx", ".xls"))
            ]
            if not files:
                raise ValueError(f"No structured data files found in directory: {uri}")
            return "csv" if files[0].endswith(".csv") else "excel"

        # For direct file or connection paths
        if uri.endswith(".csv"):
            return "csv"
        elif uri.endswith((".xlsx", ".xls")):
            return "excel"
        elif uri.startswith(("postgresql://", "mysql://", "sqlite://")):
            return "sql"
        elif "docs.google.com/spreadsheets" in uri:
            return "gsheet"
        else:
            raise ValueError(f"Unsupported structured data source: {uri}")

    def _create_sql_connector(self, uri: str, request: StructuredQueryInput):
        """Create appropriate SQL connector based on URI and request parameters"""
        parsed = urlparse(uri)
        db_type = parsed.scheme

        # Base config with common fields
        config = {
            "host": parsed.hostname,
            "port": parsed.port,
            "database": parsed.path.lstrip("/"),
            "username": parsed.username,
            "password": parsed.password,
        }

        # Add table if provided in request
        if request.table:
            config["table"] = request.table

        # Add where clause if provided in request
        if request.where:
            config["where"] = [[f.column, f.operator, f.value] for f in request.where]

        logger.info(f"DB Config: {config}")

        if db_type == "mysql":
            return MySQLConnector(config=config)
        elif db_type == "postgresql":
            return PostgreSQLConnector(config=config)
        elif db_type == "sqlite":
            return SqliteConnector(
                config={
                    "database": parsed.path,
                    "table": request.table,
                    "where": config.get("where"),
                }
            )
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    def _get_response_reformat_llm(self, query: str, response: Any):
        if response is None or query is None:
            raise ValueError("Query and response are required")

        if isinstance(response, str):
            response = response.replace("\n", " ")
        elif isinstance(response, list):
            response = ", ".join(response)
        elif isinstance(response, dict):
            response = json.dumps(response)
        else:
            # Serialize response to string
            response = str(response)

        payload = RESPONSE_REFORMAT_QUERY.format(query=query, response=response)
        return [HumanMessage(content=payload)]

    @post("/answer")
    async def answer(
        self, request: StructuredQueryInput = Body(openapi_examples=EXAMPLES)
    ):
        """Handle queries for structured data using PandasAI"""
        try:
            # Get data source
            client = await get_client()
            logger.info(f"Getting data source from FQN: {request.data_source_fqn}")
            data_source = await client.aget_data_source_from_fqn(
                request.data_source_fqn
            )
            if not data_source:
                raise HTTPException(
                    status_code=404,
                    detail=f"Data source {request.data_source_fqn} not found",
                )

            # Get source type
            source_type = self._detect_source_type(data_source.uri)

            # Get LLM
            pandas_ai_llm = model_gateway.get_pandas_ai_model_from_model_config(
                request.model_configuration
            )

            # Create a temp dir for charts
            chart_dir = tempfile.mkdtemp()

            # PandasAI config
            pandas_ai_config = {
                "llm": pandas_ai_llm,
                "save_charts": True,
                "save_charts_path": chart_dir,
            }

            # Create PandasAI agent based on source type
            if source_type in ["csv", "excel"]:
                # Use loader for CSV/Excel files
                loader = get_loader_for_data_source(DataSourceType.STRUCTURED)
                dfs = loader.get_dataframes(request.data_source_fqn)
                if dfs is None:
                    # Load the data if not cached
                    async for _ in loader.load_filtered_data(
                        data_source=data_source,
                        dest_dir=tempfile.mkdtemp(),
                        previous_snapshot={},
                        batch_size=1,
                        data_ingestion_mode=DataIngestionMode.NONE,
                    ):
                        pass
                    dfs = loader.get_dataframes(request.data_source_fqn)

                if not dfs:
                    raise Exception(
                        f"Failed to load data for {request.data_source_fqn}"
                    )

                # Create agent with multiple dataframes
                agent = Agent(
                    dfs,  # Pass list of dataframes
                    config=pandas_ai_config,
                    description=request.description,
                )

            elif source_type == "sql":
                # Create appropriate SQL connector with request parameters
                connector = self._create_sql_connector(data_source.uri, request)
                agent = Agent(
                    connector,
                    config=pandas_ai_config,
                    description=request.description,
                )

            # FIX: Not that efficient.
            # elif source_type == "gsheet":
            #     logger.info(f"Using Google Sheets connector for {data_source.uri}")
            #     # Let PandasAI handle Google Sheets directly
            #     agent = Agent(
            #         data_source.uri,
            #         config=pandas_ai_config,
            #         description=request.description,
            #     )

            else:
                raise ValueError(f"Unsupported data source type: {source_type}")

            # Get answer
            response = agent.chat(request.query)
            logger.info(f"Raw response: {response}")

            # Reformat response to a natural language using llm
            reformat_llm = model_gateway.get_llm_from_model_config(
                request.model_configuration
            )
            reformat_prompt = self._get_response_reformat_llm(request.query, response)
            response = (await reformat_llm.ainvoke(reformat_prompt)).content
            logger.info(f"Formatted response: {response}")

            # Check if there is an image in the chart dir, if so, load the image as bytes
            chart_files = [
                f
                for f in os.listdir(chart_dir)
                if os.path.isfile(os.path.join(chart_dir, f))
            ]
            if chart_files:
                image_base64 = None
                try:
                    with open(os.path.join(chart_dir, chart_files[0]), "rb") as f:
                        image_data = f.read()
                        # Encode image data as base64
                        image_base64 = base64.b64encode(image_data).decode("utf-8")
                except Exception as e:
                    logger.exception(f"Error encoding image to base64: {e}")
                finally:
                    # Clean up the individual file
                    os.remove(os.path.join(chart_dir, chart_files[0]))
                    # Clean up the temp directory
                    os.rmdir(chart_dir)
                return Answer(content=response, image_base64=image_base64)
            else:
                # Clean up the temp directory
                os.rmdir(chart_dir)
                # Return response without image
                return Answer(content=response)

        except Exception as e:
            logger.exception(f"Error in structured query: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to process structured query: {str(e)}"
            )
