from app.ai.embedding import generate_query_embedding
from app.ai.sparse_embedding import generate_sparse_query_embedding

from app.ai.qdrant_service import (
    search_similar_chunks,
    search_sparse_chunks,
)

from app.ai.hybrid_retrieval import reciprocal_rank_fusion
from app.ai.reranking import rerank_results


def test_retrieval_comparison():

    user_id = 2
    document_id = 11

    question = "What is the vehicle registration number?"

    # 1. Generate query vectors
    dense_vector = generate_query_embedding(question)
    sparse_vector = generate_sparse_query_embedding(question)

    # 2. Dense retrieval
    dense_results = search_similar_chunks(
        query_embedding=dense_vector,
        user_id=user_id,
        document_id=document_id,
        top_k=20,
    )

    # 3. Sparse retrieval
    sparse_results = search_sparse_chunks(
        query_sparse_embedding=sparse_vector,
        user_id=user_id,
        document_id=document_id,
        top_k=20,
    )

    # 4. Combine results using RRF
    hybrid_results = reciprocal_rank_fusion(
        dense_results=dense_results,
        sparse_results=sparse_results,
        top_k=10,
    )

    print("\n========== RRF RESULTS ==========")

    for rank, result in enumerate(hybrid_results, start=1):
        print(
            f"Rank: {rank} | "
            f"Chunk: {result.get('chunk_id')} | "
            f"RRF Score: {result['rrf_score']:.6f}"
        )

    # 5. Rerank RRF candidates using cross-encoder
    reranked_results = rerank_results(
        question=question,
        candidate_results=hybrid_results,
        top_k=5,
    )

    print("\n========== CROSS-ENCODER RERANKED RESULTS ==========")

    for result in reranked_results:
        print(
            f"\nRank: {result['rerank_rank']}"
            f"\nChunk: {result.get('chunk_id')}"
            f"\nCross-Encoder Score: "
            f"{result['cross_encoder_score']:.6f}"
            f"\nPrevious RRF Score: "
            f"{result['rrf_score']:.6f}"
        )

        print("Text:", result.get("chunk_text", "")[:400])


if __name__ == "__main__":
    test_retrieval_comparison()