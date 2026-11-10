
import os
import mysql.connector
from mysql.connector import Error

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

TARGET_DATABASE = "proofpocket_db"

# Read the SSL certificate path from .env
SSL_CA = os.getenv("DB_SSL_CA") or os.getenv("SSL_CA")

if not all([DB_HOST, DB_USER, DB_PASSWORD]):
    raise ValueError(
        "Missing DB_HOST, DB_USER, or DB_PASSWORD in .env"
    )

connection = None

try:
    config = {
        "host": DB_HOST,
        "port": DB_PORT,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "connection_timeout": 15,
    }

    if SSL_CA:
        if not os.path.exists(SSL_CA):
            raise FileNotFoundError(
                f"SSL certificate not found: {SSL_CA}"
            )
        config["ssl_ca"] = SSL_CA
        config["ssl_verify_cert"] = True
        config["ssl_verify_identity"] = True

    connection = mysql.connector.connect(**config)

    if not connection.is_connected():
        raise RuntimeError("Could not connect to Aiven MySQL")

    print("Successfully connected to Aiven MySQL!")

    cursor = connection.cursor()

    cursor.execute("SELECT VERSION()")
    print("MySQL version:", cursor.fetchone()[0])

    cursor.execute("SHOW DATABASES")
    databases = [row[0] for row in cursor.fetchall()]

    print("\nAvailable databases:")
    for database in databases:
        print("-", database)

    if TARGET_DATABASE in databases:
        print(f"\n{TARGET_DATABASE} already exists.")
    else:
        print(f"\nChecking permission to create {TARGET_DATABASE}...")

        try:
            cursor.execute(
                f"CREATE DATABASE `{TARGET_DATABASE}`"
            )
            connection.commit()
            print(f"SUCCESS: Created {TARGET_DATABASE}!")

        except Error as error:
            print("Could not create the database.")
            print("MySQL response:", error)

    cursor.close()

except Error as error:
    print("MySQL connection error:", error)

except Exception as error:
    print("Error:", error)

finally:
    if connection and connection.is_connected():
        connection.close()
        print("\nDatabase connection closed.")
