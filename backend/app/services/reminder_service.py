
from app.database.connection import get_db_connection


def create_reminder(user_id: int, reminder_data: dict):
    """Create a reminder only for a document owned by the current user."""

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Verify that the document belongs to this user.
        cursor.execute(
            """
            SELECT document_id
            FROM documents
            WHERE document_id = %s AND user_id = %s
            """,
            (reminder_data["document_id"], user_id),
        )

        document = cursor.fetchone()

        if not document:
            raise LookupError("Document not found or access denied.")

        cursor.execute(
            """
            INSERT INTO reminders (
                document_id,
                reminder_title,
                reminder_type,
                due_date,
                notify_at,
                status
            )
            VALUES (%s, %s, %s, %s, %s, 'pending')
            """,
            (
                reminder_data["document_id"],
                reminder_data["reminder_title"],
                reminder_data["reminder_type"],
                reminder_data["due_date"],
                reminder_data["notify_at"],
            ),
        )

        reminder_id = cursor.lastrowid
        connection.commit()

        return get_reminder(user_id, reminder_id)

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def get_user_reminders(user_id: int):
    """Return all reminders for documents owned by this user."""

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT r.*
            FROM reminders r
            INNER JOIN documents d
                ON r.document_id = d.document_id
            WHERE d.user_id = %s
            ORDER BY r.due_date ASC, r.reminder_id DESC
            """,
            (user_id,),
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def get_reminder(user_id: int, reminder_id: int):
    """Get one reminder after checking document ownership."""

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT r.*
            FROM reminders r
            INNER JOIN documents d
                ON r.document_id = d.document_id
            WHERE r.reminder_id = %s AND d.user_id = %s
            """,
            (reminder_id, user_id),
        )

        reminder = cursor.fetchone()

        if not reminder:
            raise LookupError("Reminder not found or access denied.")

        return reminder

    finally:
        cursor.close()
        connection.close()


def update_reminder(
    user_id: int,
    reminder_id: int,
    update_data: dict
):
    """Update only the supplied reminder fields."""

    allowed_fields = {
        "reminder_title",
        "reminder_type",
        "due_date",
        "notify_at",
        "status",
    }

    updates = {
        key: value
        for key, value in update_data.items()
        if key in allowed_fields and value is not None
    }

    if not updates:
        return get_reminder(user_id, reminder_id)

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT r.reminder_id
            FROM reminders r
            INNER JOIN documents d
                ON r.document_id = d.document_id
            WHERE r.reminder_id = %s AND d.user_id = %s
            """,
            (reminder_id, user_id),
        )

        if not cursor.fetchone():
            raise LookupError("Reminder not found or access denied.")

        set_clause = ", ".join(
            f"{field} = %s" for field in updates
        )

        values = list(updates.values())
        values.extend([reminder_id, user_id])

        cursor.execute(
            f"""
            UPDATE reminders r
            INNER JOIN documents d
                ON r.document_id = d.document_id
            SET {set_clause}
            WHERE r.reminder_id = %s AND d.user_id = %s
            """,
            tuple(values),
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

    return get_reminder(user_id, reminder_id)


def delete_reminder(user_id: int, reminder_id: int):
    """Delete a reminder only if its document belongs to this user."""

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            DELETE r
            FROM reminders r
            INNER JOIN documents d
                ON r.document_id = d.document_id
            WHERE r.reminder_id = %s AND d.user_id = %s
            """,
            (reminder_id, user_id),
        )

        if cursor.rowcount == 0:
            raise LookupError("Reminder not found or access denied.")

        connection.commit()
        return {"success": True, "message": "Reminder deleted successfully."}

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()
