
import logging
from uuid import UUID

from app.database.connection import get_db_connection
logger = logging.getLogger(__name__)


def save_chat_exchange(
    conversation_id: UUID,
    user_id: int,
    document_id: int | None,
    question: str,
    answer: str,
) -> None:
    """
    Save one user question and its assistant answer
    in the same database transaction.
    """

    connection = get_db_connection()
    cursor = None

    try:
        cursor = connection.cursor()

        # Check whether this conversation already exists.
        cursor.execute(
            """
            SELECT user_id, document_id
            FROM chat_history
            WHERE conversation_id = %s
            LIMIT 1
            """,
            (str(conversation_id),),
        )

        existing = cursor.fetchone()

        if existing:
            existing_user_id, existing_document_id = existing

            if existing_user_id != user_id:
                raise PermissionError(
                    "You cannot access this conversation."
                )

            if existing_document_id != document_id:
                raise ValueError(
                    "Document ID cannot be changed within a conversation."
                )

        # Save the user's question.
        cursor.execute(
            """
            INSERT INTO chat_history (
                conversation_id,
                user_id,
                document_id,
                message_role,
                message_content
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                str(conversation_id),
                user_id,
                document_id,
                "user",
                question,
            ),
        )

        # Save the assistant's answer.
        cursor.execute(
            """
            INSERT INTO chat_history (
                conversation_id,
                user_id,
                document_id,
                message_role,
                message_content
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                str(conversation_id),
                user_id,
                document_id,
                "assistant",
                answer,
            ),
        )

        connection.commit()

        logger.info(
            "Chat exchange saved for user_id=%s, conversation_id=%s",
            user_id,
            conversation_id,
        )

    except Exception:
        connection.rollback()
        logger.exception("Failed to save chat exchange")
        raise

    finally:
        if cursor:
            cursor.close()

        connection.close()


def get_chat_history(
    conversation_id: UUID,
    user_id: int,
):
    """
    Retrieve messages belonging to a conversation
    owned by the authenticated user.
    """

    connection = get_db_connection()
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                chat_id,
                conversation_id,
                document_id,
                message_role,
                message_content,
                created_at
            FROM chat_history
            WHERE conversation_id = %s
              AND user_id = %s
            ORDER BY created_at ASC, chat_id ASC
            """,
            (str(conversation_id), user_id),
        )

        return cursor.fetchall()

    finally:
        if cursor:
            cursor.close()

        connection.close()


def get_user_conversations(user_id: int):
    """
    Retrieve all conversations belonging to a user.
    """

    connection = get_db_connection()
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                conversation_id,
                document_id,
                COUNT(*) AS message_count,
                MAX(created_at) AS last_message_at
            FROM chat_history
            WHERE user_id = %s
            GROUP BY conversation_id, document_id
            ORDER BY last_message_at DESC
            """,
            (user_id,),
        )

        return cursor.fetchall()

    finally:
        if cursor:
            cursor.close()

        connection.close()
