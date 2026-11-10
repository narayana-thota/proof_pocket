import logging

from app.ai.embedding import generate_query_embedding
from app.ai.sparse_embedding import generate_sparse_query_embedding
from app.ai.qdrant_service import search_similar_chunks, search_sparse_chunks
from app.ai.hybrid_retrieval import reciprocal_rank_fusion
from app.ai.reranking import rerank_results
from app.ai.context_builder import build_context

logger = logging.getLogger(__name__)

DEFAULT_RETRIEVAL_LIMIT = 20
DEFAULT_CONTEXT_CHUNKS = 5


def retrieve_and_build_context(
    question: str,
    user_id: int,
    document_id: int | None = None,
    retrieval_limit: int = DEFAULT_RETRIEVAL_LIMIT,
    final_top_k: int = DEFAULT_CONTEXT_CHUNKS,
    max_context_chars: int = 12000,
) -> dict:
    """
    Retrieve document chunks with dense and sparse search, fuse the rankings,
    rerank candidates, and construct a source-labelled context for the LLM.
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question must be a non-empty string.")
    if user_id <= 0:
        raise ValueError("user_id must be greater than zero.")
    if retrieval_limit < 1 or final_top_k < 1:
        raise ValueError("Retrieval limits must be greater than zero.")
    if final_top_k > retrieval_limit:
        raise ValueError("final_top_k cannot exceed retrieval_limit.")
    if max_context_chars < 1:
        raise ValueError("max_context_chars must be greater than zero.")

    question = question.strip()
    logger.info(
        "Starting RAG retrieval: user_id=%s document_id=%s question=%r",
        user_id, document_id, question[:160],
    )

    dense_query_vector = generate_query_embedding(question)
    sparse_query_vector = generate_sparse_query_embedding(question)

    dense_results = search_similar_chunks(
        query_embedding=dense_query_vector,
        user_id=user_id,
        document_id=document_id,
        top_k=retrieval_limit,
    )
    sparse_results = search_sparse_chunks(
        query_sparse_embedding=sparse_query_vector,
        user_id=user_id,
        document_id=document_id,
        top_k=retrieval_limit,
    )

    fused_results = reciprocal_rank_fusion(
        dense_results=dense_results,
        sparse_results=sparse_results,
        top_k=retrieval_limit,
    )
    reranked_results = rerank_results(
        question=question,
        candidate_results=fused_results,
        top_k=final_top_k,
    )
    context_result = build_context(
        retrieved_chunks=reranked_results,
        max_context_chars=max_context_chars,
    )

    logger.info(
        "RAG retrieval counts: dense=%d sparse=%d fused=%d reranked=%d "
        "context_sources=%d context_chars=%d",
        len(dense_results), len(sparse_results), len(fused_results),
        len(reranked_results), context_result["total_sources"],
        context_result["total_characters"],
    )

    # Log metadata only. Avoid logging full document text or personal data.
    for source in context_result["sources"]:
        logger.debug(
            "RAG source: document_id=%s chunk_id=%s chunk_index=%s "
            "rrf_score=%s rerank_score=%s",
            source.get("document_id"),
            source.get("chunk_id"),
            source.get("chunk_index"),
            source.get("retrieval_score"),
            source.get("cross_encoder_score"),
        )

    return {
        "question": question,
        "context": context_result["context"],
        "sources": context_result["sources"],
        "total_sources": context_result["total_sources"],
        "retrieval_details": {
            "dense_results_count": len(dense_results),
            "sparse_results_count": len(sparse_results),
            "fused_results_count": len(fused_results),
            "reranked_results_count": len(reranked_results),
            "context_sources_count": context_result["total_sources"],
            "context_characters": context_result["total_characters"],
        },
    }
