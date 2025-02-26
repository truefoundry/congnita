from abc import ABC, abstractmethod
from typing import List

from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from langchain.schema.vectorstore import VectorStore

from backend.constants import DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE
from backend.logger import logger
from backend.types import DataPointVector


class BaseVectorDB(ABC):
    @abstractmethod
    def create_collection(self, collection_name: str, embeddings: Embeddings = None):
        """
        Create a collection in the vector database
        """
        raise NotImplementedError()

    @abstractmethod
    def upsert_documents(
        self,
        collection_name: str,
        documents: List[Document],
        embeddings: Embeddings,
        incremental: bool = True,
    ):
        """
        Upsert documents into the vector database
        """
        raise NotImplementedError()

    @abstractmethod
    def get_collections(self) -> List[str]:
        """
        Get all collection names from the vector database
        """
        raise NotImplementedError()

    @abstractmethod
    def delete_collection(self, collection_name: str):
        """
        Delete a collection from the vector database
        """
        raise NotImplementedError()

    @abstractmethod
    def get_vector_store(
        self, collection_name: str, embeddings: Embeddings
    ) -> VectorStore:
        """
        Get vector store
        """
        raise NotImplementedError()

    @abstractmethod
    def get_vector_client(self):
        """
        Get vector client
        """
        raise NotImplementedError()

    @abstractmethod
    def list_data_point_vectors(
        self,
        collection_name: str,
        data_source_fqn: str,
        batch_size: int = DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE,
    ) -> List[DataPointVector]:
        """
        Get vectors from the collection
        """
        raise NotImplementedError()

    @abstractmethod
    def delete_data_point_vectors(
        self,
        collection_name: str,
        data_point_vectors: List[DataPointVector],
        batch_size: int = DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE,
    ):
        """
        Delete vectors from the collection
        """
        raise NotImplementedError()

    def get_embedding_dimensions(self, embeddings: Embeddings) -> int:
        """
        Fetch embedding dimensions
        """
        # Calculate embedding size
        logger.debug("Embedding a dummy doc to get vector dimensions")
        partial_embeddings = embeddings.embed_documents(["Initial document"])
        vector_size = len(partial_embeddings[0])
        logger.debug(f"Vector size: {vector_size}")
        return vector_size
