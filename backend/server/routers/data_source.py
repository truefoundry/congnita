import os
import shutil
from urllib.parse import unquote

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from truefoundry.ml import get_client as get_tfy_client

from backend.constants import DataSourceType
from backend.logger import logger
from backend.modules.metadata_store.base import BaseMetadataStore
from backend.modules.metadata_store.client import get_client
from backend.settings import settings
from backend.types import CreateDataSource

router = APIRouter(prefix="/v1/data_source", tags=["data_source"])


@router.get("")
async def get_data_source():
    """Get data sources"""
    metadata_store_client: BaseMetadataStore = await get_client()
    data_sources = await metadata_store_client.aget_data_sources()
    return JSONResponse(
        content={"data_sources": [obj.model_dump() for obj in data_sources]}
    )


@router.get("/list")
async def list_data_sources():
    """Get data sources"""
    metadata_store_client: BaseMetadataStore = await get_client()
    data_sources = await metadata_store_client.alist_data_sources()
    return JSONResponse(content={"data_sources": data_sources})


@router.post("")
async def add_data_source(data_source: CreateDataSource):
    """Create a data source for the given collection"""
    metadata_store_client: BaseMetadataStore = await get_client()
    # Validate URI before creating the data source
    if data_source.type == DataSourceType.TRUEFOUNDRY:
        try:
            # Log into TrueFoundry
            tfy_client = get_tfy_client()
            # TODO: Currently, if a TFY data directory does not exist, an exception is thrown.
            # We need to raise a 404 error instead of failing generically.
            data_dir = tfy_client.get_data_directory_by_fqn(data_source.uri)
        except Exception as e:
            return JSONResponse(
                content={"error": f"Invalid DataSource URI: {e}"}, status_code=400
            )
    # Create the data source record
    created_data_source = await metadata_store_client.acreate_data_source(
        data_source=data_source
    )
    # Return the created data source
    return JSONResponse(
        content={"data_source": created_data_source.model_dump()}, status_code=201
    )


@router.delete("/delete")
async def delete_data_source(
    data_source_fqn: str,
):
    """Delete a data source"""
    metadata_store_client: BaseMetadataStore = await get_client()
    deleted_data_source = await metadata_store_client.adelete_data_source(
        unquote(data_source_fqn)
    )

    # Upon successful deletion of the data source, delete the data from `/users_data` directory if data source is of type `localdir`
    if deleted_data_source.type in [DataSourceType.LOCAL, DataSourceType.STRUCTURED]:
        data_source_uri = deleted_data_source.uri
        # data_source_uri is of the form: `/app/users_data/folder_name`
        folder_name = data_source_uri.split("/")[-1]
        folder_path = os.path.join(settings.LOCAL_DATA_DIRECTORY, folder_name)
        logger.info(
            f"Deleting folder: {folder_path}, path exists: {os.path.exists(folder_path)}"
        )
        # If the folder does not exist, skip deleting it
        if not os.path.exists(folder_path):
            logger.error(f"Folder does not exist: {folder_path}")
        else:
            # Delete the folder
            shutil.rmtree(folder_path)
            logger.info(f"Deleted folder: {folder_path}")

    if deleted_data_source.type in [
        DataSourceType.TRUEFOUNDRY,
        DataSourceType.STRUCTURED,
    ]:
        # Delete the data directory from truefoundry data directory
        try:
            # Log into TrueFoundry
            tfy_client = get_tfy_client()
            # When the data source is of type `truefoundry`, the uri contains the fqn of the data directory
            # Fetch the data directory object
            data_directory = tfy_client.get_data_directory_by_fqn(
                deleted_data_source.uri
            )
            # Delete the data directory
            data_directory.delete(delete_contents=True)
            logger.info(f"Deleted data directory: {data_directory}")
        except Exception as e:
            logger.exception(f"Failed to delete data directory: {e}")

    return JSONResponse(content={"deleted": True})
