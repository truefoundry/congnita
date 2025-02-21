import os
import re
import uuid
from types import SimpleNamespace
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from truefoundry.ml import DataDirectory
from truefoundry.ml import get_client as get_tfy_client
from truefoundry.ml.autogen.client.models.signed_url_dto import SignedURLDto

from backend.constants import DataSourceType
from backend.logger import logger
from backend.modules.model_gateway.model_gateway import model_gateway
from backend.server.routers.data_source import add_data_source
from backend.settings import settings
from backend.types import CreateDataSource, ModelType, UploadToDataDirectoryDto
from backend.utils import _get_read_signed_url

router = APIRouter(prefix="/v1/internal", tags=["internal"])


@router.post("/upload-to-local-directory")
async def upload_to_docker_directory(
    upload_name: str = Form(
        default_factory=lambda: str(uuid.uuid4()), regex=r"^[a-z][a-z0-9-]*$"
    ),
    files: List[UploadFile] = File(...),
    is_structured: bool = Form(default=False),
):
    """This function uploads files within `settings.LOCAL_DATA_DIRECTORY`"""
    if not settings.LOCAL:
        return JSONResponse(
            content={"error": "API only supported for local docker environment"},
            status_code=500,
        )
    logger.info(f"Uploading files to directory: {upload_name}")

    # Validate files if structured data
    if is_structured:
        if not files[0].filename.endswith((".csv", ".xlsx", ".xls")):
            return JSONResponse(
                content={
                    "error": "Structured data upload only supports CSV and Excel files"
                },
                status_code=400,
            )

    # create a folder within `/volumes/user_data/` that maps to `/app/user_data/` in the docker volume
    # this folder will be used to store the uploaded files
    folder_path = os.path.realpath(
        os.path.join(settings.LOCAL_DATA_DIRECTORY, upload_name)
    )
    if not folder_path.startswith(settings.LOCAL_DATA_DIRECTORY):
        return JSONResponse(
            content={"error": "Invalid upload path"},
            status_code=400,
        )

    # Create the folder if it does not exist, else raise an exception
    if os.path.exists(folder_path):
        return JSONResponse(
            content={"error": f"Folder already exists: {upload_name}"},
            status_code=500,
        )

    # Create the folder by the given name
    os.makedirs(folder_path)

    # Upload the files to the folder
    for file in files:
        logger.info(f"Copying file: {file.filename}, to folder: {folder_path}")
        file_path = os.path.realpath(os.path.join(folder_path, file.filename))
        if not file_path.startswith(folder_path):
            return JSONResponse(
                content={"error": "Invalid file path during upload"},
                status_code=400,
            )

        with open(file_path, "wb") as f:
            f.write(file.file.read())

    # Add the data source to the metadata store with appropriate type
    data_source_type = (
        DataSourceType.STRUCTURED if is_structured else DataSourceType.LOCAL
    )

    return await add_data_source(
        CreateDataSource(
            type=data_source_type,
            uri=folder_path,
        )
    )


@router.post("/upload-to-data-directory")
async def upload_to_data_directory(req: UploadToDataDirectoryDto):
    # Log into TrueFoundry
    tfy_client = get_tfy_client()
    # Create a new data directory.
    dataset = tfy_client.create_data_directory(
        settings.ML_REPO_NAME,
        req.upload_name,
    )
    # Get the signed urls for the write operation.
    _artifacts_repo = DataDirectory.from_fqn(fqn=dataset.fqn)._get_artifacts_repo()
    urls: List[SignedURLDto] = _artifacts_repo.get_signed_urls_for_write(
        artifact_identifier=SimpleNamespace(
            artifact_version_id=None, dataset_fqn=dataset.fqn
        ),
        paths=req.filepaths,
    )
    # Serialize the signed urls.
    data = [url.dict() for url in urls]
    return JSONResponse(
        content={"data": data, "data_directory_fqn": dataset.fqn},
    )


@router.get("/models")
def get_enabled_models(
    model_type: Optional[ModelType] = Query(default=None),
):
    if model_type == ModelType.embedding:
        enabled_models = model_gateway.get_embedding_models()
    elif model_type == ModelType.chat:
        enabled_models = model_gateway.get_llm_models()
    elif model_type == ModelType.reranking:
        enabled_models = model_gateway.get_reranker_models()
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model type: {model_type}",
        )

    # Serialized models
    serialized_models = [model.model_dump() for model in enabled_models]
    return JSONResponse(
        content={"models": serialized_models},
    )


@router.get("/get_signed_url")
def get_signed_url(
    data_point_fqn: str = Query(...),
):
    """
    Enrich the metadata with the signed url
    """
    # Use a single regex to extract both data-dir FQN and file path
    match = re.search(r"(data-dir:[^:]+).*?(files/.+)$", data_point_fqn)

    # Return if the regex does not match
    if not match:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid data point fqn: {data_point_fqn}",
        )

    # Extract the data-dir FQN and the file path from the FQN with source
    data_dir_fqn, file_path = match.groups()

    # Generate a signed url for the file
    signed_url_info: List[SignedURLDto] = _get_read_signed_url(
        fqn=data_dir_fqn,
        file_path=file_path,
        cache={},
    )

    # Add the signed url to the metadata if it's not None
    if not signed_url_info:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate signed url for {data_point_fqn}",
        )

    return JSONResponse(
        content={
            "signed_url": signed_url_info[0].signed_url,
        }
    )
