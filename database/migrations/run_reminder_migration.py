
from pathlib import Path
import sys

# Make the project backend package available
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.database.connection import get_db_connection

MIGRATION_FILE = (
    PROJECT_ROOT
    / "database"
    / "migrations"
    / "reminder_suggestions_migration.sql"
)

connection = None
cursor = None

try:
    if not MIGRATION_FILE.exists():
        raise FileNotFoundError(
            f"Migration file not found: {MIGRATION_FILE}"
        )

    migration_sql = MIGRATION_FILE.read_text(encoding="utf-8")

    connection = get_db_connection()
    cursor = connection.cursor()

    # Execute each statement separately.
    statements = [
        statement.strip()
        for statement in migration_sql.split(";")
        if statement.strip()
    ]

    for statement in statements:
        cursor.execute(statement)

    connection.commit()

    print("Reminder suggestions migration completed successfully!")

    cursor.execute(
        "SHOW TABLES LIKE 'reminder_suggestions'"
    )

    if cursor.fetchone():
        print("Verified: reminder_suggestions table exists.")
    else:
        print("Warning: table verification returned no result.")

except Exception as error:
    if connection:
        connection.rollback()

    print(f"Migration failed: {error}")
    raise

finally:
    if cursor:
        cursor.close()

    if connection and connection.is_connected():
        connection.close()
