
from app.ai.rag_pipeline import retrieve_and_build_context


def test_rag_pipeline():

    question = "What is the vehicle registration number?"

    result = retrieve_and_build_context(
        question=question,
        user_id=2,
        document_id=11,
        retrieval_limit=20,
        final_top_k=5,
        max_context_chars=12000,
    )

    print("\n========== RAG PIPELINE RESULT ==========")

    print("\nQuestion:")
    print(result["question"])

    print("\nRetrieval Details:")
    print(result["retrieval_details"])

    print("\nTotal Sources:")
    print(result["total_sources"])

    print("\nGenerated Context:")
    print(result["context"])

    print("\nSource References:")

    for source in result["sources"]:
        print(source)

    assert isinstance(result["context"], str)
    assert result["total_sources"] > 0
    assert len(result["sources"]) == result["total_sources"]

    print("\nRAG pipeline integration successful!")


if __name__ == "__main__":
    test_rag_pipeline()
