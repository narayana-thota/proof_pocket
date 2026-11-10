
from app.ai.qdrant_service import get_qdrant_client, COLLECTION_NAME


def verify_sparse_backfill():
    client = get_qdrant_client()

    # Get the total number of points.
    count_result = client.count(
        collection_name=COLLECTION_NAME,
        exact=True
    )

    print("Total Qdrant points:", count_result.count)

    # Retrieve sample points with their vectors and payloads.
    points, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=3,
        with_payload=True,
        with_vectors=True
    )

    for point in points:
        print("\n--- Point Verification ---")
        print("Point ID:", point.id)
        print("Document ID:", point.payload.get("document_id"))
        print("Chunk ID:", point.payload.get("chunk_id"))
        print("Chunk text exists:", bool(point.payload.get("chunk_text")))

        print("Vector data type:", type(point.vector).__name__)

        if isinstance(point.vector, dict):
            print("Vector names:", list(point.vector.keys()))

            if "sparse" in point.vector:
                sparse = point.vector["sparse"]
                print("Sparse indices:", len(sparse.indices))
                print("Sparse weights:", len(sparse.values))
                print("Sparse vector exists: YES")
            else:
                print("Sparse vector exists: NO")

        else:
            print("Returned vector:", type(point.vector).__name__)


if __name__ == "__main__":
    verify_sparse_backfill()
