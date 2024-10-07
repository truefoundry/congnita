from typing import Any, Dict, List

import weaviate
import weaviate.classes as wvc
from langchain.embeddings.base import Embeddings
from langchain_weaviate.vectorstores import WeaviateVectorStore
from langchain_core.documents import Document

from backend.constants import DATA_POINT_FQN_METADATA_KEY
from backend.modules.vector_db.base import BaseVectorDB
from backend.types import DataPointVector, VectorDBConfig
from backend.logger import logger

BATCH_SIZE = 1000
MAX_SCROLL_LIMIT = int(1e6)

def decapitalize(s):
    if not s:
        return s
    return s[0].lower() + s[1:]


class WeaviateVectorDB(BaseVectorDB):
    def __init__(self, config: VectorDBConfig):
        logger.debug(f"[Weaviate] Connecting using config: {config.model_dump()}")
        if config.local is True:
            self.weaviate_client = weaviate.connect_to_local()
        else:
            self.weaviate_client = weaviate.connect_to_weaviate_cloud(
                cluster_url=config.url,
                auth_credentials=wvc.init.Auth.api_key(config.api_key)
            )

    def create_collection(self, collection_name: str, embeddings: Embeddings):
        logger.debug(f"[Weaviate] Creating new collection {collection_name}")
        self.weaviate_client.collections.create(
            name=collection_name.capitalize(),
            replication_config=wvc.config.Configure.replication(
                factor=1
            ),
            vectorizer_config=wvc.config.Configure.Vectorizer.none(),
            properties=[
                wvc.config.Property(name=DATA_POINT_FQN_METADATA_KEY, data_type=wvc.config.DataType.TEXT)
            ]
        )
        logger.debug(f"[Weaviate] Created new collection {collection_name}")

    def _get_records_to_be_updated(self, collection_name: str, data_point_fqns: List[str]):
        logger.debug(
            f"[Weaviate] Incremental Ingestion: Fetching documents for {len(data_point_fqns)} data point fqns for collection {collection_name}"
        )
        stop = False
        offset = 0 
        record_ids_to_be_updated = []
        while stop is not True:
            records = self.weaviate_client.collections \
                .get(collection_name.capitalize()).query \
                .fetch_objects(
                    limit=BATCH_SIZE, 
                    filters=wvc.query.Filter.by_property(DATA_POINT_FQN_METADATA_KEY).contains_any(data_point_fqns),
                    offset=offset,
                    return_properties=[DATA_POINT_FQN_METADATA_KEY]
                )
            if not records or len(records.objects) < BATCH_SIZE or len(record_ids_to_be_updated) > MAX_SCROLL_LIMIT:
                stop = True
            for record in records.objects:
                record_ids_to_be_updated.append(record.uuid)
            offset += BATCH_SIZE
        logger.debug(
            f"[Weaviate] Incremental Ingestion: collection={collection_name} Addition={len(data_point_fqns)}, Updates={len(record_ids_to_be_updated)}"
        )
        return record_ids_to_be_updated          

    def upsert_documents(
        self,
        collection_name: str,
        documents: List[Document],
        embeddings: Embeddings,
        incremental: bool = True,
    ):
        """
        Upsert documents to the collection
        Arguments:
        - collection_name: Name of the collection
        - documents: List of documents
        - embeddings: Embeddings object
        - incremental: If True, the documents will be added incrementally, otherwise the collection will be replaced
        Returns:
        - None
        """
        if len(documents) == 0:
            logger.warning("No documents to index")
            return 
        logger.debug(
            f"[Weaviate] Adding {len(documents)} documents to collection {collection_name}"
        )

        data_point_fqns = []
        for document in documents:
            if document.metadata.get(DATA_POINT_FQN_METADATA_KEY):
                data_point_fqns.append(
                    document.metadata.get(DATA_POINT_FQN_METADATA_KEY)
                )
        records_to_be_updated:List[str]
        if incremental:
            records_to_be_updated = self._get_records_to_be_updated(collection_name, data_point_fqns)

        WeaviateVectorStore.from_documents(
            documents=documents,
            embedding=embeddings,
            client=self.weaviate_client,
            index_name=collection_name.capitalize(),
        )
        logger.debug(
            f"[Weaviate] Added {len(documents)} documents to collection {collection_name}"
        )

        if len(records_to_be_updated) > 0:
            logger.debug(
                f"[Weaviate] Deleting {len(records_to_be_updated)} outdated documents from collection {collection_name}"
            )
            collection = self.weaviate_client.collections.get(collection_name.capitalize())
            for i in range(0, len(records_to_be_updated), BATCH_SIZE):
                record_ids_to_be_processed = records_to_be_updated[i : i + BATCH_SIZE]
                collection.data.delete_many(
                    where=wvc.query.Filter.by_id().contains_any(record_ids_to_be_processed)
                )
            logger.debug(
                f"[Weaviate] Deleted {len(records_to_be_updated)} outdated documents from collection {collection_name}"
            )

    def get_collections(self) -> List[str]:
        collections = self.weaviate_client.collections.list_all(simple=True)
        return list(collections.keys())

    def delete_collection(
        self,
        collection_name: str,
    ):
        return self.weaviate_client.collections.delete(collection_name.capitalize())

    def get_vector_store(self, collection_name: str, embeddings: Embeddings):
        return WeaviateVectorStore(
            client=self.weaviate_client,
            embedding=embeddings,
            index_name=collection_name.capitalize(),  # Weaviate stores the index name as capitalized
            text_key="text",
            by_text=False,
            attributes=[f"{DATA_POINT_FQN_METADATA_KEY}"],
        )

    def get_vector_client(self):
        return self.weaviate_client

    def list_data_point_vectors(
        self,
        collection_name: str,
        data_source_fqn: str,
        batch_size: int = 1000,
    ) -> List[DataPointVector]:
        document_vector_points: List[DataPointVector] = []
        return document_vector_points

    def delete_data_point_vectors(
        self,
        collection_name: str,
        data_point_vectors: List[DataPointVector],
        batch_size: int = 100,
    ):
        pass
