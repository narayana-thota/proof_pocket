
from qdrant_client import models

from app.ai.qdrant_service import get_qdrant_client, COLLECTION_NAME


SPARSE_VECTOR_NAME = "sparse"


def configure_sparse_vector():
    client = get_qdrant_client()

    # Inspect the current collection configuration.
    info = client.get_collection(collection_name=COLLECTION_NAME)
    sparse_config = info.config.params.sparse_vectors or {}

    # Avoid creating the same vector configuration twice.
    if SPARSE_VECTOR_NAME in sparse_config:
        existing = sparse_config[SPARSE_VECTOR_NAME]

        if existing.modifier != models.Modifier.IDF:
            raise RuntimeError(
                "The existing sparse vector does not use the IDF modifier."
            )

        print("Sparse vector is already configured with IDF.")
        return

    # Add a named sparse vector without replacing dense vectors.
    client.create_vector_name(
        collection_name=COLLECTION_NAME,
        vector_name=SPARSE_VECTOR_NAME,
        vector_name_config=models.SparseVectorNameConfig(
            sparse=models.SparseVectorConfig(
                modifier=models.Modifier.IDF
            )
        )
    )

    # Verify the updated collection.
    updated_info = client.get_collection(
        collection_name=COLLECTION_NAME
    )

    updated_sparse_config = updated_info.config.params.sparse_vectors

    if SPARSE_VECTOR_NAME not in updated_sparse_config:
        raise RuntimeError("Sparse vector configuration was not created.")

    print("Sparse vector configured successfully!")
    print("Collection:", COLLECTION_NAME)
    print("Sparse vector:", SPARSE_VECTOR_NAME)
    print("Modifier:", updated_sparse_config[SPARSE_VECTOR_NAME].modifier)
    print("Dense vector configuration:", updated_info.config.params.vectors)


if __name__ == "__main__":
    configure_sparse_vector()
