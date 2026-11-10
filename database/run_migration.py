from app.database.connection import get_db_connection

connection = None
cursor = None

try:
    connection = get_db_connection()
    cursor = connection.cursor()

    migration_sql = """
        ALTER TABLE documents
        ADD COLUMN indexing_status
        ENUM('pending', 'processing', 'completed', 'failed')
        NOT NULL DEFAULT 'pending'
        AFTER processing_status
    """

    cursor.execute(migration_sql)
    connection.commit()

    print("Migration completed successfully!")
    print("indexing_status column added.")

except Exception:
    if connection:
        connection.rollback()
    raise

finally:
    if cursor:
        cursor.close()

    if connection and connection.is_connected():
        connection.close()