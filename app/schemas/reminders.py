from datetime import datetime

from pydantic import Field

from app.db.models import RecurrenceType
from app.schemas.base import AppSchema


class ReminderCreate(AppSchema):
    category_id: int | None = None
    title: str = Field(min_length=2, max_length=255)
    description: str | None = None
    remind_at: datetime
    recurrence: RecurrenceType = RecurrenceType.ONCE


class ReminderUpdate(AppSchema):
    category_id: int | None = None
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    remind_at: datetime | None = None
    recurrence: RecurrenceType | None = None
    is_active: bool | None = None


class ReminderRead(AppSchema):
    id: int
    user_id: int
    category_id: int | None
    title: str
    description: str | None
    remind_at: datetime
    next_run_at: datetime
    recurrence: RecurrenceType
    is_active: bool
    created_at: datetime
    updated_at: datetime
