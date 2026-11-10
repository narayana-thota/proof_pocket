
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


ReminderType = Literal["warranty", "expiry", "renewal", "custom"]


class ReminderCreate(BaseModel):
    document_id: int = Field(gt=0)
    reminder_title: str = Field(min_length=1, max_length=255)
    reminder_type: ReminderType = "custom"
    due_date: date
    notify_at: datetime


class ReminderUpdate(BaseModel):
    reminder_title: str | None = Field(
        default=None, min_length=1, max_length=255
    )
    reminder_type: ReminderType | None = None
    due_date: date | None = None
    notify_at: datetime | None = None
    status: Literal["pending", "completed", "cancelled"] | None = None
