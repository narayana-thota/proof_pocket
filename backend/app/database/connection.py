
import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

# Load .env when running outside Docker.
# Docker Compose already provides these environment variables.
load_dotenv()


def get_db_connection():

    db_config = {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
        "connection_timeout": 15
    }

    # Validate required configuration
    required_fields = ["host", "user", "password", "database"]

    missing_fields = [
        field for field in required_fields
        if not db_config.get(field)
    ]

    if missing_fields:
        raise ValueError(
            f"Missing database configuration: {missing_fields}"
        )

    # Configure SSL for Aiven MySQL
    ssl_ca = os.getenv("DB_SSL_CA") or os.getenv("SSL_CA")

    if ssl_ca:
        ssl_path = Path(ssl_ca)

        if not ssl_path.is_absolute():
            ssl_path = Path("/app") / ssl_path

        if not ssl_path.exists():
            raise FileNotFoundError(
                f"MySQL SSL certificate not found: {ssl_path}"
            )

        db_config["ssl_ca"] = str(ssl_path)
        db_config["ssl_verify_cert"] = True
        db_config["ssl_verify_identity"] = True

    connection = mysql.connector.connect(**db_config)

    return connection
