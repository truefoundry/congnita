from typing import List, Optional
from urllib.parse import urlparse

from langchain.embeddings.base import Embeddings
from langchain_community.vectorstores.qdrant import Qdrant
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams

from backend.constants import DATA_POINT_FQN_METADATA_KEY, DATA_POINT_HASH_METADATA_KEY
from backend.logger import logger
from backend.modules.vector_db.base import BaseVectorDB
from backend.types import DataPointVector, QdrantVectorDBConfig

MAX_SCROLL_LIMIT = int(1e6)
BATCH_SIZE = 1000


class QdrantVectorDB(BaseVectorDB):
    def __init__(self, db_config: QdrantVectorDBConfig):
        logger.debug(f"Connecting to qdrant using config: {db_config.model_dump()}")
        self.qdrant_client = self._create_client(db_config)

    def _create_client(self, db_config: QdrantVectorDBConfig) -> QdrantClient:
        # Local
        if db_config.local:
            return QdrantClient(path=db_config.path)

        url = db_config.url

        if url.startswith(("http://", "https://")):
            db_config.config.port = self._get_port(url, db_config.config.port)

        # If the Qdrant server is hosted on a remote server, create an http client
        return QdrantClient(
            url=url, api_key=db_config.api_key, **db_config.config.model_dump()
        )

    @staticmethod
    def _get_port(url: str, existing_port: Optional[int]) -> int:
        if existing_port:
            return existing_port

        parsed_port = urlparse(url).port
        if parsed_port:
            return parsed_port

        return 443 if url.startswith("https://") else 6333

    def create_collection(self, collection_name: str, embeddings: Embeddings):
        logger.debug(f"[Qdrant] Creating new collection {collection_name}")

        # Calculate embedding size
        partial_embeddings = embeddings.embed_documents(["Initial document"])
        vector_size = len(partial_embeddings[0])
        logger.debug(f"Vector size: {vector_size}")

        self.qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,  # embedding dimension
                distance=Distance.COSINE,
                on_disk=True,
            ),
            replication_factor=3,
        )
        self.qdrant_client.create_payload_index(
            collection_name=collection_name,
            field_name=f"metadata.{DATA_POINT_FQN_METADATA_KEY}",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        logger.debug(f"[Qdrant] Created new collection {collection_name}")

    def _get_records_to_be_upserted(
        self, collection_name: str, data_point_fqns: List[str], incremental: bool
    ):
        if not incremental:
            return []
        # For incremental deletion, we delete the documents with the same document_id
        logger.debug(
            f"[Qdrant] Incremental Ingestion: Fetching documents for {len(data_point_fqns)} data point fqns for collection {collection_name}"
        )
        stop = False
        offset = None
        record_ids_to_be_upserted = []
        while stop is not True:
            records, next_offset = self.qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=models.Filter(
                    should=[
                        models.FieldCondition(
                            key=f"metadata.{DATA_POINT_FQN_METADATA_KEY}",
                            match=models.MatchAny(
                                any=data_point_fqns,
                            ),
                        ),
                    ]
                ),
                limit=BATCH_SIZE,
                offset=offset,
                with_payload=False,
                with_vectors=False,
            )
            for record in records:
                record_ids_to_be_upserted.append(record.id)
                if len(record_ids_to_be_upserted) > MAX_SCROLL_LIMIT:
                    stop = True
                    break
            if next_offset is None:
                stop = True
            else:
                offset = next_offset

        logger.debug(
            f"[Qdrant] Incremental Ingestion: collection={collection_name} Addition={len(data_point_fqns)}, Updates={len(record_ids_to_be_upserted)}"
        )
        return record_ids_to_be_upserted

    def upsert_documents(
        self,
        collection_name: str,
        documents: list,
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
        # Get the record ids to be upserted
        record_ids_to_be_upserted: List[str] = self._get_records_to_be_upserted(
            collection_name=collection_name,
            data_point_fqns=data_point_fqns,
            incremental=incremental,
        )

        # Add Documents
        Qdrant(
            client=self.qdrant_client,
            collection_name=collection_name,
            embeddings=embeddings,
        ).add_documents(documents=documents)
        logger.debug(
            f"[Qdrant] Added {len(documents)} documents to collection {collection_name}"
        )

        # Delete old documents

        # If there are no record ids to be upserted, return
        if not len(record_ids_to_be_upserted):
            return

        logger.debug(
            f"[Qdrant] Deleting {len(documents)} outdated documents from collection {collection_name}"
        )
        for i in range(0, len(record_ids_to_be_upserted), BATCH_SIZE):
            record_ids_to_be_processed = record_ids_to_be_upserted[i : i + BATCH_SIZE]
            self.qdrant_client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=record_ids_to_be_processed,
                ),
            )
        logger.debug(
            f"[Qdrant] Deleted {len(documents)} outdated documents from collection {collection_name}"
        )

    def get_collections(self) -> List[str]:
        logger.debug("[Qdrant] Fetching collections")
        collections = self.qdrant_client.get_collections().collections
        logger.debug(f"[Qdrant] Fetched {len(collections)} collections")
        return [collection.name for collection in collections]

    def delete_collection(self, collection_name: str):
        logger.debug(f"[Qdrant] Deleting {collection_name} collection")
        self.qdrant_client.delete_collection(collection_name=collection_name)
        logger.debug(f"[Qdrant] Deleted {collection_name} collection")

    def get_vector_store(self, collection_name: str, embeddings: Embeddings):
        logger.debug(f"[Qdrant] Getting vector store for collection {collection_name}")
        return Qdrant(
            client=self.qdrant_client,
            embeddings=embeddings,
            collection_name=collection_name,
        )

    def get_vector_client(self):
        logger.debug("[Qdrant] Getting Qdrant client")
        return self.qdrant_client

    def list_data_point_vectors(
        self, collection_name: str, data_source_fqn: str, batch_size: int = BATCH_SIZE
    ) -> List[DataPointVector]:
        logger.debug(
            f"[Qdrant] Listing all data point vectors for collection {collection_name}"
        )
        stop = False
        offset = None
        data_point_vectors: List[DataPointVector] = []
        while stop is not True:
            records, next_offset = self.qdrant_client.scroll(
                collection_name=collection_name,
                limit=batch_size,
                with_payload=[
                    f"metadata.{DATA_POINT_FQN_METADATA_KEY}",
                    f"metadata.{DATA_POINT_HASH_METADATA_KEY}",
                ],
                scroll_filter=models.Filter(
                    should=[
                        models.FieldCondition(
                            key=f"metadata.{DATA_POINT_FQN_METADATA_KEY}",
                            match=models.MatchText(
                                text=data_source_fqn,
                            ),
                        ),
                    ]
                ),
                with_vectors=False,
                offset=offset,
            )
            for record in records:
                metadata: dict = record.payload.get("metadata", {})
                if metadata.get(DATA_POINT_FQN_METADATA_KEY) and metadata.get(
                    DATA_POINT_HASH_METADATA_KEY
                ):
                    data_point_vectors.append(
                        DataPointVector(
                            data_point_vector_id=record.id,
                            data_point_fqn=metadata.get(DATA_POINT_FQN_METADATA_KEY),
                            data_point_hash=metadata.get(DATA_POINT_HASH_METADATA_KEY),
                        )
                    )
                if len(data_point_vectors) > MAX_SCROLL_LIMIT:
                    stop = True
                    break
            if next_offset is None:
                stop = True
            else:
                offset = next_offset
        logger.debug(
            f"[Qdrant] Listing {len(data_point_vectors)} data point vectors for collection {collection_name}"
        )
        return data_point_vectors

    def delete_data_point_vectors(
        self,
        collection_name: str,
        data_point_vectors: List[DataPointVector],
        batch_size: int = BATCH_SIZE,
    ):
        """
        Delete data point vectors from the collection
        """
        logger.debug(f"[Qdrant] Deleting {len(data_point_vectors)} data point vectors")
        vectors_to_be_deleted_count = len(data_point_vectors)
        deleted_vectors_count = 0
        for i in range(0, vectors_to_be_deleted_count, batch_size):
            data_point_vectors_to_be_processed = data_point_vectors[i : i + batch_size]
            self.qdrant_client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=[
                        document_vector_point.data_point_vector_id
                        for document_vector_point in data_point_vectors_to_be_processed
                    ],
                ),
            )
            deleted_vectors_count = deleted_vectors_count + len(
                data_point_vectors_to_be_processed
            )
            logger.debug(
                f"[Qdrant] Deleted [{deleted_vectors_count}/{vectors_to_be_deleted_count}] data point vectors"
            )
        logger.debug(
            f"[Qdrant] Deleted {vectors_to_be_deleted_count} data point vectors"
        )

    def list_documents_in_collection(
        self, collection_name: str, base_document_id: str = None
    ) -> List[str]:
        """
        List all documents in a collection
        """
        logger.debug(
            f"[Qdrant] Listing all documents with base document id {base_document_id} for collection {collection_name}"
        )
        stop = False
        offset = None
        document_ids_set = set()
        while stop is not True:
            records, next_offset = self.qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=models.Filter(
                    should=(
                        [
                            models.FieldCondition(
                                key=f"metadata.{DATA_POINT_FQN_METADATA_KEY}",
                                match=models.MatchText(
                                    text=base_document_id,
                                ),
                            ),
                        ]
                        if base_document_id
                        else None
                    )
                ),
                limit=BATCH_SIZE,
                with_payload=[f"metadata.{DATA_POINT_FQN_METADATA_KEY}"],
                with_vectors=False,
                offset=offset,
            )
            for record in records:
                if record.payload.get("metadata") and record.payload.get(
                    "metadata"
                ).get(DATA_POINT_FQN_METADATA_KEY):
                    document_ids_set.add(
                        record.payload.get("metadata").get(DATA_POINT_FQN_METADATA_KEY)
                    )
                if len(document_ids_set) > MAX_SCROLL_LIMIT:
                    stop = True
                    break
            if next_offset is None:
                stop = True
            else:
                offset = next_offset
        logger.debug(
            f"[Qdrant] Found {len(document_ids_set)} documents with base document id {base_document_id} for collection {collection_name}"
        )
        return list(document_ids_set)

    def delete_documents(self, collection_name: str, document_ids: List[str]):
        """
        Delete documents from the collection
        """
        logger.debug(
            f"[Qdrant] Deleting {len(document_ids)} documents from collection {collection_name}"
        )
        try:
            self.qdrant_client.get_collection(collection_name=collection_name)
        except Exception as exp:
            logger.debug(exp)
            return
        # https://qdrant.tech/documentation/concepts/filtering/#full-text-match

        for i in range(0, len(document_ids), BATCH_SIZE):
            document_ids_to_be_processed = document_ids[i : i + BATCH_SIZE]
            self.qdrant_client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key=f"metadata.{DATA_POINT_FQN_METADATA_KEY}",
                                match=models.MatchAny(any=document_ids_to_be_processed),
                            ),
                        ],
                    )
                ),
            )
        logger.debug(
            f"[Qdrant] Deleted {len(document_ids)} documents from collection {collection_name}"
        )

    def list_document_vector_points(
        self, collection_name: str
    ) -> List[DataPointVector]:
        """
        List all documents in a collection
        """
        logger.debug(
            f"[Qdrant] Listing all document vector points for collection {collection_name}"
        )
        stop = False
        offset = None
        document_vector_points: List[DataPointVector] = []
        while stop is not True:
            records, next_offset = self.qdrant_client.scroll(
                collection_name=collection_name,
                limit=BATCH_SIZE,
                with_payload=[
                    f"metadata.{DATA_POINT_FQN_METADATA_KEY}",
                    f"metadata.{DATA_POINT_HASH_METADATA_KEY}",
                ],
                with_vectors=False,
                offset=offset,
            )
            for record in records:
                metadata: dict = record.payload.get("metadata")
                if (
                    metadata
                    and metadata.get(DATA_POINT_FQN_METADATA_KEY)
                    and metadata.get(DATA_POINT_HASH_METADATA_KEY)
                ):
                    document_vector_points.append(
                        DataPointVector(
                            point_id=record.id,
                            document_id=metadata.get(DATA_POINT_FQN_METADATA_KEY),
                            document_hash=metadata.get(DATA_POINT_HASH_METADATA_KEY),
                        )
                    )
                if len(document_vector_points) > MAX_SCROLL_LIMIT:
                    stop = True
                    break
            if next_offset is None:
                stop = True
            else:
                offset = next_offset
        logger.debug(
            f"[Qdrant] Listing {len(document_vector_points)} document vector points for collection {collection_name}"
        )
        return document_vector_points
