import os
import time
from typing import AsyncGenerator, Dict, List, Tuple

import pandas as pd
from pandasai import Agent
from truefoundry.ml import get_client as get_tfy_client

from backend.logger import logger
from backend.modules.dataloaders.loader import BaseDataLoader
from backend.types import DataIngestionMode, DataSource, LoadedDataPoint
from backend.utils import unzip_file


class CacheItem:
    """Class to hold cached item with timestamp"""

    def __init__(self, items: List[any]):
        self.items = items
        self.timestamp = time.time()


class StructuredLoader(BaseDataLoader):
    """
    Load structured data from various sources (CSV, Excel, and Databases)
    """

    _instance = None
    CACHE_TTL = 300  # 5 minutes in seconds

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StructuredLoader, cls).__new__(cls)
            cls._instance.dataframes = {}  # Cache for lists of dataframes
            cls._instance.agents = {}  # Cache for PandasAI agents
            cls._instance._last_cleanup = time.time()
        return cls._instance

    def _load_file(self, filepath: str) -> pd.DataFrame:
        """Load data from CSV or Excel file"""
        file_extension = os.path.splitext(filepath)[1].lower()

        if file_extension == ".csv":
            return pd.read_csv(filepath)
        elif file_extension in [".xlsx", ".xls"]:
            return pd.read_excel(filepath)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")

    def _load_files_from_directory(
        self, directory: str
    ) -> List[Tuple[str, pd.DataFrame]]:
        """Load all structured data files from a directory"""
        dataframes = []
        files = [
            f for f in os.listdir(directory) if f.endswith((".csv", ".xlsx", ".xls"))
        ]

        for file in files:
            file_path = os.path.join(directory, file)
            try:
                df = self._load_file(file_path)
                dataframes.append((file, df))
            except Exception as e:
                logger.warning(f"Failed to load file {file}: {e}")
                continue

        return dataframes

    def _cleanup_cache(self):
        """Remove expired items from cache"""
        current_time = time.time()

        # Only run cleanup every minute to avoid too frequent checks
        if current_time - self._last_cleanup < 60:
            return

        expired_dfs = [
            fqn
            for fqn, item in self.dataframes.items()
            if current_time - item.timestamp > self.CACHE_TTL
        ]
        expired_agents = [
            fqn
            for fqn, item in self.agents.items()
            if current_time - item.timestamp > self.CACHE_TTL
        ]

        # Remove expired items
        for fqn in expired_dfs:
            logger.debug(f"Removing expired dataframe from cache: {fqn}")
            del self.dataframes[fqn]

        for fqn in expired_agents:
            logger.debug(f"Removing expired agent from cache: {fqn}")
            del self.agents[fqn]

        self._last_cleanup = current_time

    def _cache_items(self, data_source_fqn: str, df: pd.DataFrame, agent: Agent):
        """Cache dataframe and agent with timestamps"""
        self.dataframes[data_source_fqn] = CacheItem(df)
        self.agents[data_source_fqn] = CacheItem(agent)

    async def load_filtered_data(
        self,
        data_source: DataSource,
        dest_dir: str,
        previous_snapshot: Dict[str, str],
        batch_size: int,
        data_ingestion_mode: DataIngestionMode,
    ) -> AsyncGenerator[List[LoadedDataPoint], None]:
        """Load structured data from source"""
        self._cleanup_cache()
        source_type = self._detect_source_type(data_source.uri)

        try:
            if source_type in ["csv", "excel"]:
                loaded_files = []  # List to store (filename, dataframe) tuples
                working_dir = None
                if data_source.uri.startswith("data-dir:"):
                    # Handle remote (TrueFoundry) files
                    tfy_files_dir = None
                    try:
                        tfy_client = get_tfy_client()
                        dataset = tfy_client.get_data_directory_by_fqn(data_source.uri)
                        working_dir = dataset.download(path=dest_dir)
                        logger.debug(f"Data directory download info: {working_dir}")

                        if os.path.exists(os.path.join(working_dir, "files")):
                            working_dir = os.path.join(working_dir, "files")

                        # Handle zip files
                        for file_name in os.listdir(working_dir):
                            if file_name.endswith(".zip"):
                                unzip_file(
                                    file_path=os.path.join(working_dir, file_name),
                                    dest_dir=working_dir,
                                )

                        loaded_files = self._load_files_from_directory(working_dir)

                    except Exception as e:
                        logger.exception(f"Error downloading data directory: {str(e)}")
                        raise ValueError(f"Failed to download data directory: {str(e)}")

                else:
                    # Handle local files
                    working_dir = (
                        data_source.uri
                        if os.path.isdir(data_source.uri)
                        else os.path.dirname(data_source.uri)
                    )
                    loaded_files = self._load_files_from_directory(working_dir)

                if not loaded_files:
                    raise Exception(f"No valid structured data files found")

                # Cache the dataframes
                self.dataframes[data_source.fqn] = CacheItem(
                    [df for _, df in loaded_files]
                )

                # Create LoadedDataPoints for each file
                data_points = []
                for filename, _ in loaded_files:
                    file_path = os.path.join(working_dir, filename)
                    data_point_hash = (
                        f"{os.path.getsize(file_path)}:{dataset.updated_at}"
                        if data_source.uri.startswith("data-dir:")
                        else str(os.lstat(file_path))
                    )

                    data_points.append(
                        LoadedDataPoint(
                            data_point_hash=data_point_hash,
                            data_point_uri=filename,
                            data_source_fqn=data_source.fqn,
                            local_filepath=file_path,
                            file_extension=os.path.splitext(filename)[1],
                            metadata={"structured_type": source_type},
                        )
                    )

                yield data_points

            elif source_type in ["sql", "gsheet"]:
                # Handle SQL and Google Sheets as before
                data_point = LoadedDataPoint(
                    data_point_hash=str(hash(data_source.uri)),
                    data_point_uri=data_source.uri,
                    data_source_fqn=data_source.fqn,
                    local_filepath=data_source.uri,
                    metadata={"structured_type": source_type},
                )
                yield [data_point]

        except Exception as e:
            logger.exception(f"Error loading structured data: {e}")
            raise

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

    def get_dataframes(self, data_source_fqn: str) -> List[pd.DataFrame]:
        """Get list of cached dataframes for a data source"""
        self._cleanup_cache()
        cached_item = self.dataframes.get(data_source_fqn)
        return cached_item.items if cached_item else None

    def get_agent(self, data_source_fqn: str) -> Agent:
        """Get cached agent for a data source"""
        self._cleanup_cache()
        cached_item = self.agents.get(data_source_fqn)
        return cached_item.items[0] if cached_item else None
