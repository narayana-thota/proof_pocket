
import os
import uuid
import math
import logging

from qdrant_client import QdrantClient, models


logger = logging.getLogger(__name__)

COLLECTION_NAME = "proofpocket_chunks"

VECTOR_DIMENSION = 384

SPARSE_VECTOR_NAME = "sparse"


def get_qdrant_client():
    """Establish a connection to Qdrant Cloud."""

    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")

    if not qdrant_url:
        raise RuntimeError("QDRANT_URL is missing from environment.")

    if not qdrant_api_key:
        raise RuntimeError("QDRANT_API_KEY is missing from environment.")

    return QdrantClient(
        url=qdrant_url,
        api_key=qdrant_api_key,
        timeout=30
    )


def create_collection():
    """
    Create the collection if needed.

    Supports both dense and sparse vectors.
    Ensures existing collections receive sparse-vector
    configuration without deleting existing data.
    """

    client = get_qdrant_client()

    if not client.collection_exists(COLLECTION_NAME):

        client.create_collection(
            collection_name=COLLECTION_NAME,

            vectors_config=models.VectorParams(
                size=VECTOR_DIMENSION,
                distance=models.Distance.COSINE
            ),

            sparse_vectors_config={
                SPARSE_VECTOR_NAME: models.SparseVectorParams(
                    modifier=models.Modifier.IDF
                )
            }
        )

        logger.info("Collection '%s' created.", COLLECTION_NAME)

    else:
        logger.info(
            "Collection '%s' already exists.",
            COLLECTION_NAME
        )

        # Inspect the existing sparse-vector configuration.
        info = client.get_collection(COLLECTION_NAME)

        sparse_config = info.config.params.sparse_vectors or {}

        if SPARSE_VECTOR_NAME not in sparse_config:

            client.create_vector_name(
                collection_name=COLLECTION_NAME,
                vector_name=SPARSE_VECTOR_NAME,

                vector_name_config=models.SparseVectorNameConfig(
                    sparse=models.SparseVectorConfig(
                        modifier=models.Modifier.IDF
                    )
                ),

                wait=True
            )

            logger.info("Sparse vector configuration added.")

    # Create indexes for metadata filtering.
    payload_indexes = {
        "user_id": models.PayloadSchemaType.INTEGER,
        "document_id": models.PayloadSchemaType.INTEGER,
        "source_type": models.PayloadSchemaType.KEYWORD
    }

    for field_name, field_type in payload_indexes.items():

        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name=field_name,
            field_schema=field_type,
            wait=True
        )

        logger.info("Payload index ready: %s", field_name)

    logger.info("Qdrant collection configuration verified.")


def verify_connection():
    """Verify the Qdrant Cloud connection."""

    client = get_qdrant_client()

    collections = client.get_collections()

    print("Qdrant Cloud connection successful.")
    print("Available collections:")

    for collection in collections.collections:
        print("-", collection.name)


def _validate_sparse_embedding(sparse_embedding: dict):
    """Validate a sparse embedding before storing or searching."""

    if not isinstance(sparse_embedding, dict):
        raise TypeError("Sparse embedding must be a dictionary.")

    indices = sparse_embedding.get("indices")
    values = sparse_embedding.get("values")

    if not isinstance(indices, list):
        raise TypeError("Sparse indices must be a list.")

    if not isinstance(values, list):
        raise TypeError("Sparse values must be a list.")

    if not indices or len(indices) != len(values):
        raise ValueError("Invalid sparse embedding dimensions.")

    if not all(
        type(index) is int and 0 <= index <= 4294967295
        for index in indices
    ):
        raise ValueError("Sparse embedding contains invalid indices.")

    if not all(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        for value in values
    ):
        raise ValueError("Sparse embedding contains invalid values.")

    return models.SparseVector(
        indices=indices,
        values=values
    )


def store_embeddings(
    processed_chunks: list[dict],
    user_id: int
) -> int:
    """
    Store dense and sparse embeddings and metadata in Qdrant.

    Both vector types are stored against the same point ID.

    Returns the number of stored points.
    """

    if type(user_id) is not int or user_id <= 0:
        raise ValueError("user_id must be a positive integer.")

    if not processed_chunks:
        return 0

    client = get_qdrant_client()

    points = []

    for chunk in processed_chunks:

        document_id = chunk["document_id"]
        chunk_index = chunk["chunk_index"]

        dense_embedding = chunk["embedding"]
        sparse_embedding = chunk["sparse_embedding"]

        if type(document_id) is not int or document_id <= 0:
            raise ValueError("Invalid document_id.")

        if type(chunk_index) is not int or chunk_index < 0:
            raise ValueError("Invalid chunk_index.")

        if not isinstance(dense_embedding, list):
            raise TypeError("Dense embedding must be a list.")

        if len(dense_embedding) != VECTOR_DIMENSION:
            raise ValueError(
                f"Expected {VECTOR_DIMENSION} dense dimensions, "
                f"received {len(dense_embedding)}."
            )

        if not all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
            for value in dense_embedding
        ):
            raise ValueError("Dense embedding contains invalid values.")

        sparse_vector = _validate_sparse_embedding(sparse_embedding)

        # Generate a deterministic UUID for each document chunk.
        point_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"proofpocket:{user_id}:{document_id}:{chunk_index}"
            )
        )

        payload = {
            "user_id": user_id,
            "document_id": document_id,
            "chunk_id": chunk["chunk_id"],
            "chunk_index": chunk_index,
            "chunk_text": chunk["chunk_text"],
            "source_type": chunk["source_type"],
            "start_token": chunk["start_token"],
            "end_token": chunk["end_token"],
            "token_count": chunk["token_count"]
        }

        # Store both named vectors.
        points.append(
            models.PointStruct(
                id=point_id,

                vector={
                    "": dense_embedding,
                    SPARSE_VECTOR_NAME: sparse_vector
                },

                payload=payload
            )
        )

    # Upsert both vectors together.
    result = client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
        wait=True
    )

    logger.info(
        "Qdrant upload status: %s. Stored points: %s",
        result.status,
        len(points)
    )

    return len(points)


def delete_document_embeddings(
    document_id: int,
    user_id: int
) -> None:
    """
    Delete all Qdrant points belonging to a specific user's document.

    Both dense and sparse vectors are deleted with their points.
    """

    if type(document_id) is not int or document_id <= 0:
        raise ValueError("Invalid document_id.")

    if type(user_id) is not int or user_id <= 0:
        raise ValueError("Invalid user_id.")

    client = get_qdrant_client()

    document_filter = models.Filter(
        must=[
            models.FieldCondition(
                key="user_id",
                match=models.MatchValue(value=user_id)
            ),
            models.FieldCondition(
                key="document_id",
                match=models.MatchValue(value=document_id)
            )
        ]
    )

    result = client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=models.FilterSelector(
            filter=document_filter
        ),
        wait=True
    )

    logger.info(
        "Qdrant deletion completed for user_id=%s, document_id=%s. Status: %s",
        user_id,
        document_id,
        result.status
    )


def search_similar_chunks(
    query_embedding: list[float],
    user_id: int,
    top_k: int = 5,
    document_id: int | None = None
) -> list[dict]:
    """
    Search for semantically similar chunks using dense vectors.

    Results are restricted to the authenticated user's documents.
    """

    if type(user_id) is not int or user_id <= 0:
        raise ValueError("Invalid user_id.")

    if type(top_k) is not int or top_k <= 0:
        raise ValueError("top_k must be a positive integer.")

    if document_id is not None:
        if type(document_id) is not int or document_id <= 0:
            raise ValueError("Invalid document_id.")

    if not isinstance(query_embedding, list):
        raise TypeError("Query embedding must be a list.")

    if len(query_embedding) != VECTOR_DIMENSION:
        raise ValueError(
            f"Expected {VECTOR_DIMENSION} dimensions, "
            f"received {len(query_embedding)}."
        )

    if not all(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        for value in query_embedding
    ):
        raise ValueError("Query embedding contains invalid values.")

    search_filter = _build_user_filter(user_id, document_id)

    client = get_qdrant_client()

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        query_filter=search_filter,
        limit=top_k,
        with_payload=True
    )

    results = []

    for point in response.points:
        payload = point.payload or {}

        results.append({
            "point_id": str(point.id),
            "document_id": payload.get("document_id"),
            "chunk_id": payload.get("chunk_id"),
            "chunk_index": payload.get("chunk_index"),
            "chunk_text": payload.get("chunk_text"),
            "source_type": payload.get("source_type"),
            "similarity_score": point.score
        })

    return results


def search_sparse_chunks(
    query_sparse_embedding: dict,
    user_id: int,
    top_k: int = 5,
    document_id: int | None = None
) -> list[dict]:
    """
    Search for keyword-relevant chunks using BM25 sparse vectors.

    Results are restricted to the authenticated user's documents.
    """

    if type(user_id) is not int or user_id <= 0:
        raise ValueError("Invalid user_id.")

    if type(top_k) is not int or top_k <= 0:
        raise ValueError("top_k must be a positive integer.")

    if document_id is not None:
        if type(document_id) is not int or document_id <= 0:
            raise ValueError("Invalid document_id.")

    sparse_vector = _validate_sparse_embedding(query_sparse_embedding)

    search_filter = _build_user_filter(user_id, document_id)

    client = get_qdrant_client()

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=sparse_vector,
        using=SPARSE_VECTOR_NAME,
        query_filter=search_filter,
        limit=top_k,
        with_payload=True
    )

    results = []

    for point in response.points:
        payload = point.payload or {}

        results.append({
            "point_id": str(point.id),
            "document_id": payload.get("document_id"),
            "chunk_id": payload.get("chunk_id"),
            "chunk_index": payload.get("chunk_index"),
            "chunk_text": payload.get("chunk_text"),
            "source_type": payload.get("source_type"),
            "sparse_score": point.score
        })

    return results


def _build_user_filter(
    user_id: int,
    document_id: int | None = None
):
    """Build a Qdrant filter for user-level and optional document-level access."""

    conditions = [
        models.FieldCondition(
            key="user_id",
            match=models.MatchValue(value=user_id)
        )
    ]

    if document_id is not None:
        conditions.append(
            models.FieldCondition(
                key="document_id",
                match=models.MatchValue(value=document_id)
            )
        )

    return models.Filter(must=conditions)


if __name__ == "__main__":
    verify_connection()
    create_collection()
