
from fastembed import SparseTextEmbedding
from qdrant_client import models

from app.ai.qdrant_service import get_qdrant_client, COLLECTION_NAME


MODEL_NAME = "Qdrant/bm25"
CACHE_DIR = "/root/.cache/huggingface/fastembed"

SPARSE_VECTOR_NAME = "sparse"

SCROLL_BATCH_SIZE = 100
EMBEDDING_BATCH_SIZE = 64


def backfill_sparse_vectors():
    client = get_qdrant_client()

    print("Loading BM25 sparse embedding model...")

    model = SparseTextEmbedding(
        model_name=MODEL_NAME,
        cache_dir=CACHE_DIR
    )

    offset = None
    total_processed = 0
    total_skipped = 0

    print("Starting sparse-vector backfill...")

    while True:
        # Retrieve existing points without downloading dense vectors.
        points, next_offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=SCROLL_BATCH_SIZE,
            offset=offset,
            with_payload=["chunk_text"],
            with_vectors=False
        )

        if not points:
            break

        valid_points = []
        texts = []

        for point in points:
            chunk_text = point.payload.get("chunk_text") or ""

            if not chunk_text.strip():
                total_skipped += 1
                continue

            valid_points.append(point)
            texts.append(chunk_text)

        # Generate sparse vectors for the current batch.
        if texts:
            embeddings = list(
                model.embed(
                    texts,
                    batch_size=EMBEDDING_BATCH_SIZE
                )
            )

            if len(embeddings) != len(valid_points):
                raise RuntimeError(
                    "Sparse embedding count does not match point count."
                )

            vector_updates = []

            for point, embedding in zip(valid_points, embeddings):
                indices = embedding.indices.tolist()
                values = embedding.values.tolist()

                if not indices:
                    total_skipped += 1
                    continue

                vector_updates.append(
                    models.PointVectors(
                        id=point.id,
                        vector={
                            SPARSE_VECTOR_NAME: models.SparseVector(
                                indices=indices,
                                values=values
                            )
                        }
                    )
                )

            # Update only the sparse vector.
            if vector_updates:
                client.update_vectors(
                    collection_name=COLLECTION_NAME,
                    points=vector_updates,
                    wait=True
                )

                total_processed += len(vector_updates)

        print(
            f"Processed: {total_processed} | "
            f"Skipped: {total_skipped}"
        )

        if next_offset is None:
            break

        offset = next_offset

    print("\n--- Backfill completed ---")
    print("Collection:", COLLECTION_NAME)
    print("Sparse vector:", SPARSE_VECTOR_NAME)
    print("Successfully updated:", total_processed)
    print("Skipped:", total_skipped)


if __name__ == "__main__":
    backfill_sparse_vectors()
