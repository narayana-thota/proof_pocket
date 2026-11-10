
import logging

from app.services.document_service import (
    get_extracted_document_text
)

from app.ai.pipeline import process_document

from app.ai.qdrant_service import store_embeddings

from app.database.connection import get_db_connection


logger = logging.getLogger(__name__)


def update_indexing_status(document_id: int, user_id: int, status: str):
    """Update the indexing status of a user's document."""

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
            UPDATE documents
            SET indexing_status = %s
            WHERE document_id = %s
              AND user_id = %s
        """

        cursor.execute(query, (status, document_id, user_id))
        connection.commit()

        if cursor.rowcount == 0:
            raise ValueError("Document not found for this user.")

    except Exception:
        if connection:
            connection.rollback()
        raise

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


def index_document(document_id: int, user_id: int) -> dict:
    """
    Retrieve extracted text, generate embeddings,
    and store them in Qdrant Cloud.
    """

    if not isinstance(document_id, int) or document_id <= 0:
        raise ValueError("Invalid document ID.")

    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("Invalid user ID.")

    indexing_started = False

    try:
        # Step 1: Retrieve extracted text from MySQL
        document = get_extracted_document_text(
            document_id=document_id,
            user_id=user_id
        )

        if not document:
            raise ValueError(
                "Document not found or extraction is incomplete."
            )

        extracted_text = document["extracted_text"]
        source_type = document["file_extension"].lower().lstrip(".")

        # Step 2: Mark indexing as processing
        update_indexing_status(
            document_id, user_id, "processing"
        )
        indexing_started = True

        # Step 3: Generate chunks and embeddings
        processed_chunks = process_document(
            extracted_text=extracted_text,
            document_id=document_id,
            source_type=source_type
        )

        if not processed_chunks:
            raise ValueError("No chunks were generated.")

        # Step 4: Store embeddings in Qdrant Cloud
        stored_count = store_embeddings(
            processed_chunks=processed_chunks,
            user_id=user_id
        )

        if stored_count != len(processed_chunks):
            raise RuntimeError(
                "Not all embeddings were stored successfully."
            )

        # Step 5: Mark indexing as completed
        update_indexing_status(
            document_id, user_id, "completed"
        )

        logger.info(
            "Document %s indexed successfully. Stored %s vectors.",
            document_id,
            stored_count
        )

        return {
            "success": True,
            "document_id": document_id,
            "user_id": user_id,
            "total_chunks": len(processed_chunks),
            "stored_vectors": stored_count,
            "indexing_status": "completed",
            "message": "Document indexed successfully."
        }

    except Exception:
        logger.exception(
            "Indexing failed for document %s", document_id
        )

        if indexing_started:
            try:
                update_indexing_status(
                    document_id, user_id, "failed"
                )
            except Exception:
                logger.exception(
                    "Could not update indexing failure status."
                )

        raise
