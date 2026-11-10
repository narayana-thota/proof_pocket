import logging

from app.ai.embedding import generate_query_embedding
from app.ai.qdrant_service import search_similar_chunks

logger = logging.getLogger(__name__)


def perform_semantic_search(
    question: str,
    user_id: int,
    top_k: int = 5,
    document_id: int | None = None
) -> list[dict]:

    # Step 1: Generate the question embedding.
    query_embedding = generate_query_embedding(question)

    # Step 2: Retrieve matching chunks from Qdrant.
    results = search_similar_chunks(
        query_embedding=query_embedding,
        user_id=user_id,
        top_k=top_k,
        document_id=document_id
    )

    logger.info(
        "Semantic search completed. User ID: %s, Results: %s",
        user_id,
        len(results)
    )

    return results