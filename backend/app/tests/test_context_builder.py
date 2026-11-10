
from app.ai.context_builder import build_context


def test_context_builder():
    retrieved_chunks = [
        {
            "chunk_id": "11_004",
            "document_id": 11,
            "chunk_index": 3,
            "chunk_text": "The insured vehicle particulars are listed here.",
            "rrf_score": 0.032,
            "dense_score": 0.54,
            "sparse_score": 4.31,
            "source_type": "pdf",
        },
        {
            "chunk_id": "11_002",
            "document_id": 11,
            "chunk_index": 1,
            "chunk_text": "The vehicle registration number is UA 07 K 5553.",
            "rrf_score": 0.031,
            "dense_score": 0.52,
            "sparse_score": 4.10,
            "source_type": "pdf",
        },
        {
            "chunk_id": "11_002",
            "document_id": 11,
            "chunk_index": 1,
            "chunk_text": "The vehicle registration number is UA 07 K 5553.",
            "rrf_score": 0.030,
            "dense_score": 0.50,
            "sparse_score": 4.00,
            "source_type": "pdf",
        },
    ]

    result = build_context(retrieved_chunks)

    assert result["total_sources"] == 2
    assert "UA 07 K 5553" in result["context"]
    assert "[Source 1" in result["context"]
    assert result["total_characters"] == len(result["context"])

    print("\nContext construction successful!")
    print("Sources:", result["total_sources"])
    print("\nGenerated context:\n")
    print(result["context"])


if __name__ == "__main__":
    test_context_builder()
