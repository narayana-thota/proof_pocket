import logging
import os
import uuid
import os
import tempfile
from pathlib import Path

from app.database.connection import get_db_connection

from app.storage.b2_storage import generate_presigned_url

from app.ai.qdrant_service import delete_document_embeddings


from app.processors.pdf_processor import extract_pdf_text

from app.processors.docx_processor import extract_docx_text

from app.processors.excel_processor import extract_excel_text
from app.storage.b2_storage import download_file
from app.processors.text_processor import extract_txt_text
from app.storage.b2_storage import (
    upload_file,
    delete_file,
    generate_presigned_url,
    B2_BUCKET_NAME
)


ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".xlsx", ".txt",
    ".jpg", ".jpeg", ".png"
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def upload_document(user_id, uploaded_file, category_id=None,
                    document_type=None):

    original_filename = Path(uploaded_file.filename or "").name
    extension = Path(original_filename).suffix.lower()

    if not original_filename or extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type.")

    # Determine file size
    uploaded_file.file.seek(0, os.SEEK_END)
    file_size = uploaded_file.file.tell()
    uploaded_file.file.seek(0)

    if file_size == 0:
        raise ValueError("Empty files are not allowed.")

    if file_size > MAX_FILE_SIZE:
        raise ValueError("File size exceeds the 10 MB limit.")

    # Generate a unique storage key
    document_uuid = str(uuid.uuid4())
    object_key = f"documents/{user_id}/{document_uuid}{extension}"

    connection = None
    cursor = None
    file_uploaded = False

    try:
        # Upload actual file to Backblaze
        upload_file(
            uploaded_file.file,
            object_key,
            uploaded_file.content_type or "application/octet-stream"
        )
        file_uploaded = True

        # Save metadata in MySQL
        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
            INSERT INTO documents (
                user_id,
                category_id,
                document_name,
                document_type,
                original_file_name,
                file_extension,
                mime_type,
                file_size_bytes,
                storage_provider,
                bucket_name,
                object_key,
                upload_status,
                processing_status,
                classification_status
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s,
                'backblaze_b2', %s, %s,
                'completed', 'pending', 'pending'
            )
        """

        values = (
            user_id,
            category_id,
            Path(original_filename).stem,
            document_type,
            original_filename,
            extension,
            uploaded_file.content_type,
            file_size,
            B2_BUCKET_NAME,
            object_key
        )

        cursor.execute(query, values)
        connection.commit()

        return {
            "success": True,
            "document_id": cursor.lastrowid,
            "document_name": Path(original_filename).stem,
            "original_file_name": original_filename,
            "file_size_bytes": file_size,
            "message": "Document uploaded successfully."
        }

    except Exception:
        if connection:
            connection.rollback()

        # Remove cloud file if database insertion fails
        if file_uploaded:
            try:
                delete_file(object_key)
            except Exception:
                pass

        raise

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

def get_user_documents(user_id):
    """
    Retrieve all documents belonging to a particular user.
    """

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                d.document_id,
                d.user_id,
                d.category_id,
                dc.category_name,
                d.document_name,
                d.document_type,
                d.original_file_name,
                d.file_extension,
                d.mime_type,
                d.file_size_bytes,
                d.upload_status,
                d.processing_status,
                d.classification_status,
                d.classification_confidence,
                d.created_at,
                d.updated_at
            FROM documents d
            LEFT JOIN document_categories dc
                ON d.category_id = dc.category_id
            WHERE d.user_id = %s
            ORDER BY d.created_at DESC
        """

        cursor.execute(query, (user_id,))

        documents = cursor.fetchall()

        return {
            "success": True,
            "total_documents": len(documents),
            "documents": documents
        }

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


def get_document_by_id(document_id, user_id):
    """
    Retrieve a particular document belonging to a user.
    """

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                d.document_id,
                d.user_id,
                d.category_id,
                dc.category_name,
                d.document_name,
                d.document_type,
                d.original_file_name,
                d.file_extension,
                d.mime_type,
                d.file_size_bytes,
                d.storage_provider,
                d.upload_status,
                d.processing_status,
                d.classification_status,
                d.classification_confidence,
                d.created_at,
                d.updated_at
            FROM documents d
            LEFT JOIN document_categories dc
                ON d.category_id = dc.category_id
            WHERE d.document_id = %s
              AND d.user_id = %s
        """

        cursor.execute(query, (document_id, user_id))

        document = cursor.fetchone()

        return document

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


from app.storage.b2_storage import generate_presigned_url


def get_document_download_url(document_id, user_id):
    """
    Generate a temporary download URL for a user's document.
    """

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                document_id,
                original_file_name,
                object_key
            FROM documents
            WHERE document_id = %s
              AND user_id = %s
              AND upload_status = 'completed'
        """

        cursor.execute(query, (document_id, user_id))
        document = cursor.fetchone()

        if not document:
            return None

        download_url = generate_presigned_url(
            object_key=document["object_key"],
            expiration=300
        )

        return {
            "document_id": document["document_id"],
            "file_name": document["original_file_name"],
            "download_url": download_url,
            "expires_in_seconds": 300
        }

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

def delete_document(document_id, user_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Step 1: Verify document ownership
        cursor.execute(
            """
            SELECT document_id, object_key
            FROM documents
            WHERE document_id = %s
              AND user_id = %s
            """,
            (document_id, user_id)
        )

        document = cursor.fetchone()

        if not document:
            return None

        object_key = document["object_key"]

        # Step 2: Delete vectors from Qdrant
        # If this fails, stop deletion and preserve MySQL records.
        delete_document_embeddings(
            document_id=document_id,
            user_id=user_id
        )

        # Step 3: Delete related MySQL records
        cursor.execute(
            "DELETE FROM extracted_data WHERE document_id = %s",
            (document_id,)
        )

        cursor.execute(
            "DELETE FROM reminders WHERE document_id = %s",
            (document_id,)
        )

        cursor.execute(
            "DELETE FROM chat_history WHERE document_id = %s",
            (document_id,)
        )

        # Step 4: Delete document metadata
        cursor.execute(
            """
            DELETE FROM documents
            WHERE document_id = %s
              AND user_id = %s
            """,
            (document_id, user_id)
        )

        connection.commit()

        # Step 5: Delete original file from Backblaze B2
        try:
            delete_file(object_key)
            storage_deleted = True

        except Exception:
            logging.exception("Backblaze file deletion failed")
            storage_deleted = False

        return {
            "success": True,
            "document_id": document_id,
            "vectors_deleted": True,
            "storage_deleted": storage_deleted,
            "message": "Document and associated vectors deleted."
        }

    except Exception:
        if connection:
            connection.rollback()

        raise

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()
            
def process_pdf_document(document_id, user_id):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # 1. Find the document and verify ownership
        cursor.execute(
            """
            SELECT document_id, object_key, file_extension
            FROM documents
            WHERE document_id = %s
              AND user_id = %s
              AND upload_status = 'completed'
            """,
            (document_id, user_id)
        )

        document = cursor.fetchone()

        if not document:
            return None

        if document["file_extension"].lower() != ".pdf":
            raise ValueError("Only PDF files are supported currently.")

        # 2. Mark processing as started
        cursor.execute(
            """
            UPDATE documents
            SET processing_status = 'processing'
            WHERE document_id = %s AND user_id = %s
            """,
            (document_id, user_id)
        )

        connection.commit()

        # 3. Extract PDF text from Backblaze
        result = extract_pdf_text(document["object_key"])

        extracted_text = result["extracted_text"]

        if not extracted_text.strip():
            raise ValueError(
                "No selectable text found. This PDF may be scanned."
            )

        # 4. Save extracted text in MySQL
        cursor.execute(
            """
            INSERT INTO extracted_data (
                document_id,
                extracted_text,
                extraction_status
            )
            VALUES (%s, %s, 'completed')

            ON DUPLICATE KEY UPDATE
                extracted_text = VALUES(extracted_text),
                extraction_status = 'completed',
                error_message = NULL
            """,
            (document_id, extracted_text)
        )

        # 5. Update document processing status
        cursor.execute(
            """
            UPDATE documents
            SET processing_status = 'completed'
            WHERE document_id = %s AND user_id = %s
            """,
            (document_id, user_id)
        )

        connection.commit()

        return {
            "success": True,
            "document_id": document_id,
            "page_count": result["page_count"],
            "extracted_character_count": len(extracted_text),
            "message": "PDF text extracted and saved successfully."
        }

    except Exception as error:

        if connection:
            connection.rollback()

        # Record extraction failure
        if connection and cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO extracted_data (
                        document_id,
                        extraction_status,
                        error_message
                    )
                    VALUES (%s, 'failed', %s)

                    ON DUPLICATE KEY UPDATE
                        extraction_status = 'failed',
                        error_message = VALUES(error_message)
                    """,
                    (document_id, str(error)[:1000])
                )

                cursor.execute(
                    """
                    UPDATE documents
                    SET processing_status = 'failed'
                    WHERE document_id = %s AND user_id = %s
                    """,
                    (document_id, user_id)
                )

                connection.commit()

            except Exception:
                connection.rollback()

        raise

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

def process_docx_document(document_id, user_id):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Verify document ownership
        cursor.execute(
            """
            SELECT document_id, object_key, file_extension
            FROM documents
            WHERE document_id = %s
              AND user_id = %s
              AND upload_status = 'completed'
            """,
            (document_id, user_id)
        )

        document = cursor.fetchone()

        if not document:
            return None

        if document["file_extension"].lower() != ".docx":
            raise ValueError("Only DOCX files are supported.")

        cursor.execute(
            """
            UPDATE documents
            SET processing_status = 'processing'
            WHERE document_id = %s
            """,
            (document_id,)
        )
        connection.commit()

        # Download the DOCX file temporarily
        import os
        import tempfile

        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(
                suffix=".docx",
                delete=False
            ) as temp_file:
                temp_path = temp_file.name

            from app.storage.b2_storage import download_file

            download_file(
                object_key=document["object_key"],
                destination_path=temp_path
            )

            # Extract text
            extracted_text = extract_docx_text(temp_path)

        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

        if not extracted_text.strip():
            raise ValueError("No text found in this DOCX document.")

        # Save extracted text
        cursor.execute(
            """
            INSERT INTO extracted_data (
                document_id,
                extracted_text,
                extraction_status
            )
            VALUES (%s, %s, 'completed')
            ON DUPLICATE KEY UPDATE
                extracted_text = VALUES(extracted_text),
                extraction_status = 'completed',
                error_message = NULL
            """,
            (document_id, extracted_text)
        )

        cursor.execute(
            """
            UPDATE documents
            SET processing_status = 'completed'
            WHERE document_id = %s
            """,
            (document_id,)
        )

        connection.commit()

        return {
            "success": True,
            "document_id": document_id,
            "extracted_character_count": len(extracted_text),
            "message": "DOCX text extracted successfully."
        }

    except Exception as error:
        if connection:
            connection.rollback()

        if connection and cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO extracted_data (
                        document_id,
                        extraction_status,
                        error_message
                    )
                    VALUES (%s, 'failed', %s)
                    ON DUPLICATE KEY UPDATE
                        extraction_status = 'failed',
                        error_message = VALUES(error_message)
                    """,
                    (document_id, str(error)[:1000])
                )

                cursor.execute(
                    """
                    UPDATE documents
                    SET processing_status = 'failed'
                    WHERE document_id = %s
                    """,
                    (document_id,)
                )

                connection.commit()

            except Exception:
                connection.rollback()

        raise

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

def process_excel_document(document_id, user_id):

    connection = None
    cursor = None
    temp_path = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT document_id, object_key, file_extension
            FROM documents
            WHERE document_id = %s
              AND user_id = %s
              AND upload_status = 'completed'
            """,
            (document_id, user_id)
        )

        document = cursor.fetchone()

        if not document:
            return None

        if document["file_extension"].lower() != ".xlsx":
            raise ValueError("Only XLSX files are supported.")

        cursor.execute(
            """
            UPDATE documents
            SET processing_status = 'processing'
            WHERE document_id = %s
            """,
            (document_id,)
        )
        connection.commit()

        with tempfile.NamedTemporaryFile(
            suffix=".xlsx",
            delete=False
        ) as temp_file:
            temp_path = temp_file.name

        download_file(
            object_key=document["object_key"],
            destination_path=temp_path
        )

        extracted_text = extract_excel_text(temp_path)

        if not extracted_text.strip():
            raise ValueError("No data found in this Excel file.")

        cursor.execute(
            """
            INSERT INTO extracted_data (
                document_id,
                extracted_text,
                extraction_status
            )
            VALUES (%s, %s, 'completed')
            ON DUPLICATE KEY UPDATE
                extracted_text = VALUES(extracted_text),
                extraction_status = 'completed',
                error_message = NULL
            """,
            (document_id, extracted_text)
        )

        cursor.execute(
            """
            UPDATE documents
            SET processing_status = 'completed'
            WHERE document_id = %s
            """,
            (document_id,)
        )

        connection.commit()

        return {
            "success": True,
            "document_id": document_id,
            "extracted_character_count": len(extracted_text),
            "message": "Excel data extracted successfully."
        }

    except Exception as error:

        if connection:
            connection.rollback()

        if connection and cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO extracted_data (
                        document_id,
                        extraction_status,
                        error_message
                    )
                    VALUES (%s, 'failed', %s)
                    ON DUPLICATE KEY UPDATE
                        extraction_status = 'failed',
                        error_message = VALUES(error_message)
                    """,
                    (document_id, str(error)[:1000])
                )

                cursor.execute(
                    """
                    UPDATE documents
                    SET processing_status = 'failed'
                    WHERE document_id = %s
                    """,
                    (document_id,)
                )

                connection.commit()

            except Exception:
                connection.rollback()

        raise

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

def process_txt_document(document_id, user_id):

    connection = None
    cursor = None
    temp_path = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # 1. Verify document ownership
        cursor.execute("""
            SELECT document_id, object_key, file_extension
            FROM documents
            WHERE document_id = %s
              AND user_id = %s
              AND upload_status = 'completed'
        """, (document_id, user_id))

        document = cursor.fetchone()

        if not document:
            return None

        # 2. Validate file extension
        if document["file_extension"].lower() != ".txt":
            raise ValueError("Only TXT files are supported.")

        # 3. Update processing status
        cursor.execute("""
            UPDATE documents
            SET processing_status = 'processing'
            WHERE document_id = %s AND user_id = %s
        """, (document_id, user_id))

        connection.commit()

        # 4. Download original file from Backblaze B2
        with tempfile.NamedTemporaryFile(
            suffix=".txt",
            delete=False
        ) as temp_file:

            temp_path = temp_file.name

        download_file(
            object_key=document["object_key"],
            destination_path=temp_path
        )

        # 5. Extract text
        extracted_text = extract_txt_text(temp_path)

        if not extracted_text.strip():
            raise ValueError("No text found in this TXT file.")

        # 6. Store extracted text in MySQL
        cursor.execute("""
            INSERT INTO extracted_data (
                document_id,
                extracted_text,
                extraction_status
            )
            VALUES (%s, %s, 'completed')

            ON DUPLICATE KEY UPDATE
                extracted_text = VALUES(extracted_text),
                extraction_status = 'completed',
                error_message = NULL
        """, (document_id, extracted_text))

        # 7. Mark document processing as completed
        cursor.execute("""
            UPDATE documents
            SET processing_status = 'completed'
            WHERE document_id = %s AND user_id = %s
        """, (document_id, user_id))

        connection.commit()

        return {
            "success": True,
            "document_id": document_id,
            "extracted_character_count": len(extracted_text),
            "message": "TXT text extracted and saved successfully."
        }

    except Exception as error:

        if connection:
            connection.rollback()

        # Record extraction failure
        if connection and cursor:
            try:
                cursor.execute("""
                    INSERT INTO extracted_data (
                        document_id,
                        extraction_status,
                        error_message
                    )
                    VALUES (%s, 'failed', %s)

                    ON DUPLICATE KEY UPDATE
                        extraction_status = 'failed',
                        error_message = VALUES(error_message)
                """, (document_id, str(error)[:1000]))

                cursor.execute("""
                    UPDATE documents
                    SET processing_status = 'failed'
                    WHERE document_id = %s AND user_id = %s
                """, (document_id, user_id))

                connection.commit()

            except Exception:
                connection.rollback()

        raise

    finally:

        # Remove temporary file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

def get_extracted_document_text(document_id: int, user_id: int):
    """
    Retrieve successfully extracted text for a user's document.
    """

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                d.document_id,
                d.user_id,
                d.file_extension,
                ed.extracted_text
            FROM documents d
            INNER JOIN extracted_data ed
                ON d.document_id = ed.document_id
            WHERE d.document_id = %s
              AND d.user_id = %s
              AND d.upload_status = 'completed'
              AND d.processing_status = 'completed'
              AND ed.extraction_status = 'completed'
        """

        cursor.execute(query, (document_id, user_id))

        result = cursor.fetchone()

        if not result:
            return None

        if not result["extracted_text"] or not result["extracted_text"].strip():
            raise ValueError("Extracted document text is empty.")

        return result

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()