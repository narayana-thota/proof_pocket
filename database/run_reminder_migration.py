from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.database.connection import get_db_connection

sql_file = ROOT / "database" / "migrations" / "reminder_suggestions_migration.sql"

conn = None
cursor = None

try:
    sql = sql_file.read_text(encoding="utf-8")
    conn = get_db_connection()
    cursor = conn.cursor()

    for statement in sql.split(";"):
        if statement.strip():
            cursor.execute(statement)

    conn.commit()
    print("SUCCESS: Reminder suggestions migration completed!")

    cursor.execute("SHOW TABLES LIKE 'reminder_suggestions'")
    print("Table verification:", cursor.fetchone())

except Exception as e:
    if conn:
        conn.rollback()
    print("MIGRATION FAILED:", e)
    raise

finally:
    if cursor:
        cursor.close()
    if conn and conn.is_connected():
        conn.close()
