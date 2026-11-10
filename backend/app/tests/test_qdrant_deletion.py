from qdrant_client import models

from app.ai.qdrant_service import (
    get_qdrant_client,
    COLLECTION_NAME
)


def verify_document_vectors(user_id, document_id):

    client = get_qdrant_client()

    result = client.count(
        collection_name=COLLECTION_NAME,
        count_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value=user_id)
                ),
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=document_id)
                )
            ]
        ),
        exact=True
    )

    print("User ID:", user_id)
    print("Document ID:", document_id)
    print("Remaining vectors:", result.count)

    return result.count


if __name__ == "__main__":
    verify_document_vectors(
        user_id=2,
        document_id=12
    )