from datetime import datetime

from pydantic import Field

from app.db.models import TaskPriority, TaskStatus
from app.schemas.base import AppSchema


class TaskCreate(AppSchema):
    title: str = Field(min_length=2, max_length=255)
    description: str | None = None
    due_at: datetime | None = None
    priority: TaskPriority = TaskPriority.NORMAL


class TaskUpdate(AppSchema):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    due_at: datetime | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None


class TaskRead(AppSchema):
    id: int
    user_id: int
    title: str
    description: str | None
    due_at: datetime | None
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
