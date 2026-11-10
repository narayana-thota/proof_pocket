from app.ai.embedding import generate_query_embedding
from app.ai.qdrant_service import search_similar_chunks


def test_user_isolation():

    document_id = 11

    question = "What are the start and end dates of this insurance policy?"

    query_vector = generate_query_embedding(question)

    # Actual owner of document 11.
    owner_results = search_similar_chunks(
        query_embedding=query_vector,
        user_id=2,
        document_id=document_id,
        top_k=5
    )

    # Another user attempting to access the same document.
    other_user_results = search_similar_chunks(
        query_embedding=query_vector,
        user_id=1,
        document_id=document_id,
        top_k=5
    )

    print("\nUSER ISOLATION TEST")
    print("=" * 50)

    print("Owner results:", len(owner_results))
    print("Other user results:", len(other_user_results))

    assert len(owner_results) > 0, "Owner should retrieve their document."

    assert len(other_user_results) == 0, (
        "Security failure: another user retrieved this document!"
    )

    print("\nPASS: User-level document isolation verified.")


if __name__ == "__main__":
    test_user_isolation()