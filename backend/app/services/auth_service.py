
from pwdlib import PasswordHash
from mysql.connector import IntegrityError, Error
from app.database.connection import get_db_connection
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4


# Create password hashing utility
password_hash = PasswordHash.recommended()


# Hash the user's password
def hash_password(password: str) -> str:
    return password_hash.hash(password)


# Verify the submitted password
def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


# Register a new user
def register_user(full_name: str, email: str, password: str):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Check whether email already exists
        cursor.execute(
            "SELECT user_id FROM users WHERE email = %s",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            return {
                "success": False,
                "message": "Email already registered."
            }

        # Hash password before storing
        hashed_password = hash_password(password)

        # Insert new user
        cursor.execute(
            """
            INSERT INTO users (full_name, email, password_hash)
            VALUES (%s, %s, %s)
            """,
            (full_name, email, hashed_password)
        )

        connection.commit()

        user_id = cursor.lastrowid

        return {
            "success": True,
            "message": "Registration successful.",
            "user": {
                "user_id": user_id,
                "full_name": full_name,
                "email": email
            }
        }

    except IntegrityError:
        if connection:
            connection.rollback()

        return {
            "success": False,
            "message": "Email already registered."
        }

    except Error:
        if connection:
            connection.rollback()
        raise

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# Authenticate an existing user
def authenticate_user(email: str, password: str):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Find user using email
        cursor.execute(
            """
            SELECT user_id, full_name, email, password_hash, is_active
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        user = cursor.fetchone()

        # Check user existence
        if not user:
            return None

        # Check account status
        if not user["is_active"]:
            return None

        # Verify password
        if not verify_password(password, user["password_hash"]):
            return None

        # Return public user information
        return {
            "user_id": user["user_id"],
            "full_name": user["full_name"],
            "email": user["email"]
        }

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

def create_user_session(user_id: int):

    connection = None
    cursor = None

    try:
        # Generate a unique session ID
        session_id = str(uuid4())

        # Calculate refresh session expiry
        expiry_days = int(
            os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
        )

        expires_at = (
            datetime.now(timezone.utc)
            + timedelta(days=expiry_days)
        ).replace(tzinfo=None)

        connection = get_db_connection()
        cursor = connection.cursor()

        # Save session in MySQL
        cursor.execute(
            """
            INSERT INTO user_sessions
            (session_id, user_id, expires_at)
            VALUES (%s, %s, %s)
            """,
            (session_id, user_id, expires_at)
        )

        connection.commit()

        return session_id

    except Error:
        if connection:
            connection.rollback()
        raise

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

# Retrieve the currently authenticated user's details
def get_user_by_id(user_id: int):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT user_id, full_name, email
            FROM users
            WHERE user_id = %s AND is_active = TRUE
            """,
            (user_id,)
        )

        return cursor.fetchone()

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# Check whether a refresh session is active
def validate_user_session(session_id: str, user_id: int) -> bool:

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT session_id
            FROM user_sessions
            WHERE session_id = %s
              AND user_id = %s
              AND revoked_at IS NULL
              AND expires_at > UTC_TIMESTAMP()
            """,
            (session_id, user_id)
        )

        return cursor.fetchone() is not None

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# Revoke a login session during logout
def revoke_user_session(session_id: str, user_id: int) -> bool:

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE user_sessions
            SET revoked_at = UTC_TIMESTAMP()
            WHERE session_id = %s
              AND user_id = %s
              AND revoked_at IS NULL
            """,
            (session_id, user_id)
        )

        connection.commit()

        return cursor.rowcount > 0

    except Error:
        if connection:
            connection.rollback()
        raise

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

