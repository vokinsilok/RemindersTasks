from datetime import datetime

from pydantic import Field

from app.schemas.base import AppSchema


class UserRead(AppSchema):
    id: int
    platform: str
    telegram_id: int | None = None
    vk_user_id: int | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    created_at: datetime
    updated_at: datetime


class TelegramUserUpsert(AppSchema):
    telegram_id: int
    username: str | None = Field(default=None, max_length=255)
    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)


class VkUserUpsert(AppSchema):
    vk_user_id: int
    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)
