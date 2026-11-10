from app.database.connection import get_db_connection

connection = None
cursor = None

try:
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            d.document_id,
            d.user_id,
            d.original_file_name,
            d.upload_status,
            d.processing_status,
            d.indexing_status,
            ed.extraction_status,
            LENGTH(ed.extracted_text) AS extracted_text_length
        FROM documents d
        LEFT JOIN extracted_data ed
            ON d.document_id = ed.document_id
        WHERE d.document_id = %s
          AND d.user_id = %s
    """

    cursor.execute(query, (11, 2))
    result = cursor.fetchone()

    print("\nDOCUMENT STATUS:")
    print(result)

finally:
    if cursor:
        cursor.close()

    if connection and connection.is_connected():
        connection.close()