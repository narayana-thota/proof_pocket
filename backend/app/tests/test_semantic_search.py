from app.ai.embedding import generate_query_embedding
from app.ai.qdrant_service import search_similar_chunks


def test_semantic_search():

    # Use an existing document belonging to user 2.
    user_id = 2
    document_id = 11

    question = "What is the vehicle registration number?"

    # Step 1: Generate question embedding.
    query_vector = generate_query_embedding(question)

    print("\nQUERY EMBEDDING")
    print("Vector dimensions:", len(query_vector))

    # Step 2: Search Qdrant.
    results = search_similar_chunks(
        query_embedding=query_vector,
        user_id=user_id,
        document_id=document_id,
        top_k=5
    )

    print("\nSEMANTIC SEARCH RESULTS")
    print("=" * 60)

    if not results:
        print("No matching chunks found.")
        return

    for result in results:
        print("Document ID:", result["document_id"])
        print("Chunk ID:", result["chunk_id"])
        print("Similarity Score:", result["similarity_score"])
        print("Chunk Text:", result["chunk_text"])
        print("-" * 60)

    print("Total retrieved chunks:", len(results))


if __name__ == "__main__":
    test_semantic_search()