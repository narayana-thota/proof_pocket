
from app.ai.qdrant_service import (
    store_embeddings,
    get_qdrant_client,
    COLLECTION_NAME
)

from app.ai.qdrant_service import (
    store_embeddings,
    get_qdrant_client,
    create_collection,
    COLLECTION_NAME
)

from qdrant_client import models


def test_store_sample_embeddings():
    create_collection()

    sample_chunks = []

    for index in range(3):
        sample_chunks.append({
            "document_id": 999,
            "chunk_id": f"999_{index + 1:03d}",
            "chunk_index": index,
            "chunk_text": f"This is sample document chunk {index + 1}.",
            "source_type": "txt",
            "start_token": index * 150,
            "end_token": (index * 150) + 180,
            "token_count": 180,
            "embedding": [0.01] * 384
        })

    stored_count = store_embeddings(
        processed_chunks=sample_chunks,
        user_id=999
    )

    print("Stored points:", stored_count)

    client = get_qdrant_client()

    result = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value=999)
                ),
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=999)
                )
            ]
        ),
        limit=10,
        with_payload=True,
        with_vectors=False
    )

    points, _ = result

    print("Retrieved points:", len(points))

    for point in points:
        print(
            point.payload["chunk_id"],
            point.payload["chunk_text"]
        )

    assert stored_count == 3
    assert len(points) == 3

    print("Qdrant storage test passed!")


if __name__ == "__main__":
    test_store_sample_embeddings()
