from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime
from typing import Literal

from app.dependencies import get_current_user
from app.schemas.reminder import ReminderCreate, ReminderUpdate
from app.services.reminder_service import (
    create_reminder,
    get_user_reminders,
    get_reminder,
    update_reminder,
    delete_reminder,
)
from app.services.ai_reminder_service import (
    get_user_reminder_suggestions,
    approve_reminder_suggestion,
    reject_reminder_suggestion,
)

router = APIRouter(prefix="/api/reminders", tags=["Reminders"])


class ReminderSuggestionApproval(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reminder_title: str | None = Field(default=None, min_length=1, max_length=255)
    reminder_type: Literal["warranty", "expiry", "renewal", "custom"] | None = None
    due_date: date | None = None
    notify_at: datetime | None = None


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_new_reminder(
    reminder: ReminderCreate,
    current_user: dict = Depends(get_current_user),
):
    try:
        result = create_reminder(current_user["user_id"], reminder.model_dump())
        return {
            "success": True,
            "message": "Reminder created successfully.",
            "reminder": result,
        }
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error))


@router.get("/")
def list_reminders(current_user: dict = Depends(get_current_user)):
    reminders = get_user_reminders(current_user["user_id"])
    return {
        "success": True,
        "total": len(reminders),
        "reminders": reminders,
    }


# Keep the fixed /suggestions route before /{reminder_id}.
@router.get("/suggestions")
def list_reminder_suggestions(
    suggestion_status: Literal["pending", "approved", "rejected", "all"] = Query(
        default="pending", alias="status"
    ),
    current_user: dict = Depends(get_current_user),
):
    suggestions = get_user_reminder_suggestions(
        user_id=current_user["user_id"],
        status=suggestion_status,
    )
    return {
        "success": True,
        "total": len(suggestions),
        "suggestions": suggestions,
    }


@router.post("/suggestions/{suggestion_id}/approve")
def approve_suggestion(
    suggestion_id: int,
    overrides: ReminderSuggestionApproval | None = None,
    current_user: dict = Depends(get_current_user),
):
    try:
        result = approve_reminder_suggestion(
            user_id=current_user["user_id"],
            suggestion_id=suggestion_id,
            overrides=overrides.model_dump(exclude_unset=True) if overrides else {},
        )
        return {
            "success": True,
            "message": "AI suggestion approved and reminder created.",
            **result,
        }
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/suggestions/{suggestion_id}/reject")
def reject_suggestion(
    suggestion_id: int,
    current_user: dict = Depends(get_current_user),
):
    try:
        return reject_reminder_suggestion(
            user_id=current_user["user_id"],
            suggestion_id=suggestion_id,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error))


@router.get("/{reminder_id}")
def retrieve_reminder(
    reminder_id: int,
    current_user: dict = Depends(get_current_user),
):
    try:
        reminder = get_reminder(current_user["user_id"], reminder_id)
        return {"success": True, "reminder": reminder}
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error))


@router.put("/{reminder_id}")
def edit_reminder(
    reminder_id: int,
    reminder: ReminderUpdate,
    current_user: dict = Depends(get_current_user),
):
    try:
        updated = update_reminder(
            current_user["user_id"],
            reminder_id,
            reminder.model_dump(exclude_unset=True),
        )
        return {
            "success": True,
            "message": "Reminder updated successfully.",
            "reminder": updated,
        }
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error))


@router.delete("/{reminder_id}")
def remove_reminder(
    reminder_id: int,
    current_user: dict = Depends(get_current_user),
):
    try:
        return delete_reminder(current_user["user_id"], reminder_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error))
