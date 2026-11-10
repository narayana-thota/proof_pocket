from app.ai.rag_pipeline import retrieve_and_build_context


def test_rag_context():

    result = retrieve_and_build_context(
        question="What is the vehicle registration number?",
        user_id=2,
        document_id=11,
    )

    print("\n========== RETRIEVED CONTEXT ==========")
    print(result["context"])

    print("\n========== SOURCE DETAILS ==========")

    for source in result["sources"]:
        print(
            f"Chunk ID: {source['chunk_id']} | "
            f"Rank: {source.get('rerank_rank')}"
        )

    print("\n========== SEARCH RESULT ==========")
    print("Registration number found:",
          "UA 07 K 5553" in result["context"]).upper()


if __name__ == "__main__":
    test_rag_context()