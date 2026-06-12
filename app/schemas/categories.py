from datetime import datetime

from pydantic import Field

from app.schemas.base import AppSchema


class CategoryCreate(AppSchema):
    title: str = Field(min_length=2, max_length=120)


class CategoryRead(AppSchema):
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime
