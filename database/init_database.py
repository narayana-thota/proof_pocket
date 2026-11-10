
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

connection = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    ssl_ca=os.getenv("DB_SSL_CA") or os.getenv("SSL_CA")
)

def execute_sql_file(cursor, file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        sql_script = file.read()

    statements = [
        statement.strip()
        for statement in sql_script.split(";")
        if statement.strip()
    ]

    for statement in statements:
        cursor.execute(statement)

try:
    cursor = connection.cursor()

    execute_sql_file(cursor, "database/schema.sql")
    print("Schema executed successfully!")

    execute_sql_file(cursor, "database/seed.sql")
    connection.commit()
    print("Category data inserted successfully!")

    cursor.execute("SHOW TABLES")
    print("\nTables in ProofPocket:")
    for row in cursor.fetchall():
        print("-", row[0])

    cursor.execute("SELECT * FROM document_categories")
    print("\nDocument categories:")
    for row in cursor.fetchall():
        print(row)

except Exception as error:
    connection.rollback()
    print("Database initialization failed:", error)

finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("\nDatabase connection closed.")
