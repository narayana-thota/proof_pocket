
from fastembed import SparseTextEmbedding
from qdrant_client import models

from app.ai.qdrant_service import get_qdrant_client, COLLECTION_NAME


MODEL_NAME = "Qdrant/bm25"
CACHE_DIR = "/root/.cache/huggingface/fastembed"


def test_sparse_embedding():
    # Initialize the BM25 sparse embedding model.
    model = SparseTextEmbedding(
        model_name=MODEL_NAME,
        cache_dir=CACHE_DIR
    )

    # Connect to the existing Qdrant collection.
    client = get_qdrant_client()

    # Retrieve one existing chunk belonging to user 2.
    search_filter = models.Filter(
        must=[
            models.FieldCondition(
                key="user_id",
                match=models.MatchValue(value=2)
            ),
            models.FieldCondition(
                key="document_id",
                match=models.MatchValue(value=11)
            )
        ]
    )

    points, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=search_filter,
        limit=1,
        with_payload=True,
        with_vectors=False
    )

    if not points:
        raise RuntimeError("No existing document chunks found.")

    chunk_text = points[0].payload.get("chunk_text")

    if not chunk_text:
        raise RuntimeError("The selected chunk has no text.")

    # Generate a sparse vector.
    sparse_embedding = list(model.embed([chunk_text]))[0]

    indices = sparse_embedding.indices.tolist()
    values = sparse_embedding.values.tolist()

    # Display the generated sparse-vector information.
    print("\n--- Sparse Embedding Results ---")
    print("Model:", MODEL_NAME)
    print("Document ID:", points[0].payload["document_id"])
    print("Chunk ID:", points[0].payload["chunk_id"])
    print("Number of active indices:", len(indices))
    print("Number of weights:", len(values))
    print("First 20 indices:", indices[:20])
    print("First 20 weights:", values[:20])

    assert len(indices) == len(values)
    assert len(indices) > 0


if __name__ == "__main__":
    test_sparse_embedding()
