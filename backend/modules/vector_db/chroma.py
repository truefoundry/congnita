from typing import List, Optional

from chromadb import HttpClient, PersistentClient
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from fastapi import HTTPException
from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from langchain_community.vectorstores import Chroma

from backend.constants import (
    DATA_POINT_FQN_METADATA_KEY,
    DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE,
)
from backend.logger import logger
from backend.modules.vector_db.base import BaseVectorDB
from backend.types import ChromaVectorDBConfig, DataPointVector


class ChromaVectorDB(BaseVectorDB):
    def __init__(self, db_config: ChromaVectorDBConfig):
        self.db_config = db_config
        self.client = self._create_client()

    ## Initialization utility

    def _create_client(self) -> ClientAPI:
        # For local development, we use a persistent client that saves data to a temporary directory
        if self.db_config.local:
            return PersistentClient()

        # For production, we use an http client that connects to a remote server
        return HttpClient(
            url=self.db_config.url,
            api_key=self.db_config.api_key,
            config=self.db_config.config,
        )

    ## Client
    def get_vector_client(self) -> ClientAPI:
        return self.client

    ## Vector store

    def get_vector_store(self, collection_name: str, **kwargs):
        return Chroma(
            client=self.client,
            collection_name=collection_name,
            **kwargs,
        )

    ## Collections

    def create_collection(self, collection_name: str, **kwargs) -> Collection:
        try:
            return self.client.create_collection(
                name=collection_name,
                **kwargs,
            )
        except ValueError as e:
            # Error is raised by chroma client if
            # 1. collection already exists
            # 2. collection name is invalid
            raise HTTPException(
                status_code=400, detail=f"Unable to create collection: {e}"
            )

    def get_collection(self, collection_name: str) -> Collection:
        return self.client.get_collection(name=collection_name)

    def delete_collection(self, collection_name: str) -> None:
        try:
            return self.client.delete_collection(name=collection_name)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Unable to delete collection. {collection_name} does not exist",
            )

    def get_collections(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[str]:
        return [
            collection.name
            for collection in self.client.list_collections(limit=limit, offset=offset)
        ]

    ## Documents

    def upsert_documents(
        self,
        collection_name: str,
        documents: List[Document],
        embeddings: Embeddings,
        incremental: bool = True,
    ):
        if not documents:
            logger.warning("No documents to index")
            return
        # get record IDs to be upserted
        logger.debug(
            f"[Qdrant] Adding {len(documents)} documents to collection {collection_name}"
        )
        # Collect the data point fqns from the documents
        data_point_fqns = [
            doc.metadata.get(DATA_POINT_FQN_METADATA_KEY)
            for doc in documents
            if doc.metadata.get(DATA_POINT_FQN_METADATA_KEY)
        ]

    def delete_documents(self, collection_name: str, document_ids: List[str]):
        # Fetch the collection
        collection: Collection = self.client.get_collection(collection_name)
        # Delete the documents in the collection by ids
        collection.delete(ids=document_ids)

    ## Data point vectors

    def list_data_point_vectors(
        self,
        collection_name: str,
        data_source_fqn: str,
        batch_size: int = DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE,
    ) -> List[DataPointVector]:
        # Fetch the collection by collection name
        collection = self.get_collection(collection_name)
        # Initialize the data point vectors list
        data_point_vectors = []
        # Initialize the offset
        offset = 0

        while True:
            # Fetch the documents from the collection and limit the fetch to batch size
            documents = collection.get(
                where={
                    "data_source_fqn": data_source_fqn,
                },
                # Only fetch the metadata and ids of the documents since we need to return the data point vectors
                include=["metadatas", "ids"],
                # Limit the fetch to `batch_size`
                limit=batch_size,
                # Offset the fetch by `offset`
                offset=offset,
            )

            # Break the loop if:
            # 1. No documents are fetched -> we've reached the end of the collection
            # 2. The number of documents fetched is less than the batch size -> we've reached the end of the collection
            if not documents["ids"] or len(documents["ids"]) < batch_size:
                break

            # Iterate over the documents and append the data point vectors to the list if the metadata contains the data source fqn and data point hash
            for doc_id, metadata in zip(documents["ids"], documents["metadatas"]):
                # TODO: what if either of the metadata keys are missing?
                if metadata.get("data_source_fqn") and metadata.get("data_point_hash"):
                    # Append the data point vector to the list
                    data_point_vectors.append(
                        DataPointVector(
                            data_point_vector_id=doc_id,
                            data_point_fqn=metadata.get("data_source_fqn"),
                            data_point_hash=metadata.get("data_point_hash"),
                        )
                    )

            # Increment the offset by the number of documents fetched
            offset += len(documents["ids"])

        return data_point_vectors

    def delete_data_point_vectors(
        self,
        collection_name: str,
        data_point_vectors: List[DataPointVector],
        **kwargs,
    ):
        # Fetch the collection by collection name
        collection = self.get_collection(collection_name)
        # Delete the documents in the collection by ids
        collection.delete(
            ids=[vector.data_point_vector_id for vector in data_point_vectors]
        )
        logger.debug(f"[Chroma] Deleted {len(data_point_vectors)} data point vectors")
