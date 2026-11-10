import json
import logging
from datetime import date, datetime, time, timedelta
from typing import Any

from app.database.connection import get_db_connection
from app.services.document_service import get_extracted_document_text
from app.ai.groq_client import generate_reminder_events

logger = logging.getLogger(__name__)

ALLOWED_TYPES = {"warranty", "expiry", "renewal", "custom"}


def _normalise_for_match(value: str) -> str:
    return " ".join(str(value).lower().split())


def _normalise_event(event: dict[str, Any]) -> dict[str, Any] | None:
    """Validate an AI event before it is persisted as a suggestion."""
    if not isinstance(event, dict):
        return None

    title = str(event.get("title") or "").strip()
    evidence = str(event.get("evidence") or "").strip()
    raw_date = str(event.get("due_date") or "").strip()

    if not title or not evidence or not raw_date:
        return None

    try:
        due_date = date.fromisoformat(raw_date)
    except ValueError:
        return None

    reminder_type = str(event.get("reminder_type") or "custom").lower()
    if reminder_type not in ALLOWED_TYPES:
        reminder_type = "custom"

    try:
        confidence = float(event.get("confidence", 0.5))
    except (TypeError, ValueError):
        confidence = 0.5
    confidence = max(0.0, min(1.0, confidence))

    # Schedule the default notification seven days before the due date,
    # at 09:00. If that date has passed, schedule it for today at 09:00.
    notify_date = due_date - timedelta(days=7)
    today = date.today()
    if notify_date < today:
        notify_date = today
    notify_at = datetime.combine(notify_date, time(hour=9, minute=0))

    return {
        "reminder_title": title[:255],
        "reminder_type": reminder_type,
        "due_date": due_date,
        "notify_at": notify_at,
        "evidence": evidence[:2000],
        "confidence": confidence,
    }


def generate_document_reminder_suggestions(user_id: int, document_id: int):
    """Generate and persist reviewable AI suggestions for an owned document."""
    document_text = get_extracted_document_text(
        document_id=document_id,
        user_id=user_id,
    )
    if not document_text:
        raise LookupError(
            "Document text is not available. Extract the document before generating reminders."
        )

    extracted_text = document_text.get("extracted_text") or ""
    if not extracted_text.strip():
        raise ValueError("The document does not contain usable extracted text.")

    # Keep the prompt within a predictable size. The model is instructed to
    # return only dates and events supported by the supplied document text.
    events = generate_reminder_events(
        document_text=extracted_text[:30000],
        current_date=date.today().isoformat(),
    )

    suggestions = []
    searchable_text = _normalise_for_match(extracted_text)
    for event in events:
        evidence = str(event.get("evidence") or "") if isinstance(event, dict) else ""
        # Only accept a suggestion when its quoted evidence can be found in
        # the extracted source text. This rejects unsupported model claims.
        if not evidence or _normalise_for_match(evidence) not in searchable_text:
            continue
        normalised = _normalise_event(event)
        if normalised:
            suggestions.append(normalised)

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Replace only previous pending suggestions for this document.
        # Approved/rejected history is preserved.
        cursor.execute(
            """
            DELETE FROM reminder_suggestions
            WHERE user_id = %s
              AND document_id = %s
              AND status = 'pending'
            """,
            (user_id, document_id),
        )

        for suggestion in suggestions:
            cursor.execute(
                """
                INSERT INTO reminder_suggestions (
                    user_id,
                    document_id,
                    reminder_title,
                    reminder_type,
                    due_date,
                    notify_at,
                    evidence,
                    confidence,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
                """,
                (
                    user_id,
                    document_id,
                    suggestion["reminder_title"],
                    suggestion["reminder_type"],
                    suggestion["due_date"],
                    suggestion["notify_at"],
                    suggestion["evidence"],
                    suggestion["confidence"],
                ),
            )

        connection.commit()

        cursor.execute(
            """
            SELECT
                suggestion_id,
                document_id,
                reminder_title,
                reminder_type,
                due_date,
                notify_at,
                evidence,
                confidence,
                status,
                created_at
            FROM reminder_suggestions
            WHERE user_id = %s
              AND document_id = %s
              AND status = 'pending'
            ORDER BY due_date ASC, suggestion_id ASC
            """,
            (user_id, document_id),
        )
        saved = cursor.fetchall()

        return {
            "success": True,
            "document_id": document_id,
            "total": len(saved),
            "suggestions": saved,
            "message": (
                "AI reminder suggestions generated."
                if saved
                else "No reliable date-based reminder events were found in this document."
            ),
        }

    except Exception:
        connection.rollback()
        logger.exception("Failed to generate or save reminder suggestions")
        raise
    finally:
        cursor.close()
        connection.close()


def get_user_reminder_suggestions(user_id: int, status: str = "pending"):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        query = """
            SELECT
                rs.suggestion_id,
                rs.document_id,
                d.document_name,
                d.original_file_name,
                rs.reminder_title,
                rs.reminder_type,
                rs.due_date,
                rs.notify_at,
                rs.evidence,
                rs.confidence,
                rs.status,
                rs.reminder_id,
                rs.created_at
            FROM reminder_suggestions rs
            INNER JOIN documents d
                ON d.document_id = rs.document_id
            WHERE rs.user_id = %s
        """
        values: list[Any] = [user_id]
        if status != "all":
            query += " AND rs.status = %s"
            values.append(status)
        query += " ORDER BY rs.created_at DESC, rs.suggestion_id DESC"

        cursor.execute(query, tuple(values))
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def approve_reminder_suggestion(
    user_id: int,
    suggestion_id: int,
    overrides: dict[str, Any] | None = None,
):
    """Atomically create a reminder and mark its suggestion approved."""
    overrides = overrides or {}
    allowed = {"reminder_title", "reminder_type", "due_date", "notify_at"}

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
                rs.*,
                d.document_id
            FROM reminder_suggestions rs
            INNER JOIN documents d
                ON d.document_id = rs.document_id
            WHERE rs.suggestion_id = %s
              AND rs.user_id = %s
              AND d.user_id = %s
            FOR UPDATE
            """,
            (suggestion_id, user_id, user_id),
        )
        suggestion = cursor.fetchone()

        if not suggestion:
            raise LookupError("AI reminder suggestion not found.")
        if suggestion["status"] != "pending":
            raise ValueError("This suggestion has already been reviewed.")

        reminder_data = {
            key: overrides.get(key, suggestion[key])
            for key in allowed
        }

        title = str(reminder_data["reminder_title"] or "").strip()
        if not title:
            raise ValueError("Reminder title cannot be empty.")
        if reminder_data["reminder_type"] not in ALLOWED_TYPES:
            raise ValueError("Invalid reminder type.")

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
                suggestion["document_id"],
                title[:255],
                reminder_data["reminder_type"],
                reminder_data["due_date"],
                reminder_data["notify_at"],
            ),
        )
        reminder_id = cursor.lastrowid

        cursor.execute(
            """
            UPDATE reminder_suggestions
            SET status = 'approved',
                reminder_id = %s
            WHERE suggestion_id = %s
              AND user_id = %s
              AND status = 'pending'
            """,
            (reminder_id, suggestion_id, user_id),
        )

        connection.commit()
        return {
            "success": True,
            "message": "AI suggestion approved and reminder created.",
            "reminder_id": reminder_id,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def reject_reminder_suggestion(user_id: int, suggestion_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            UPDATE reminder_suggestions rs
            INNER JOIN documents d
                ON d.document_id = rs.document_id
            SET rs.status = 'rejected'
            WHERE rs.suggestion_id = %s
              AND rs.user_id = %s
              AND d.user_id = %s
              AND rs.status = 'pending'
            """,
            (suggestion_id, user_id, user_id),
        )
        if cursor.rowcount == 0:
            raise LookupError("Pending AI reminder suggestion not found.")
        connection.commit()
        return {
            "success": True,
            "message": "AI reminder suggestion rejected.",
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()
