
from app.ai.sparse_embedding import generate_sparse_query_embedding
from app.ai.qdrant_service import search_sparse_chunks


def test_sparse_search():
    user_id = 2
    document_id = 11

    question = "What is the vehicle registration number?"

    # Step 1: Generate sparse query embedding.
    query_vector = generate_sparse_query_embedding(question)

    print("\nQuestion:", question)
    print("Sparse query dimensions:", len(query_vector["indices"]))

    # Step 2: Search Qdrant using sparse vectors.
    results = search_sparse_chunks(
        query_sparse_embedding=query_vector,
        user_id=user_id,
        document_id=document_id,
        top_k=5
    )

    print("\n--- BM25 Search Results ---")
    print("Total results:", len(results))

    for rank, result in enumerate(results, start=1):
        print(f"\nRank: {rank}")
        print("Chunk ID:", result["chunk_id"])
        print("Score:", result["sparse_score"])
        print("Text:", result["chunk_text"][:500])

    assert len(results) > 0, "No sparse search results returned."


if __name__ == "__main__":
    test_sparse_search()
