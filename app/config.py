from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str | None = None
    vk_group_id: int | None = None
    vk_group_token: str | None = None
    vk_api_version: str = "5.199"
    database_url: str = "postgresql+asyncpg://reminders:reminders@localhost:5432/reminders_tasks"
    scheduler_poll_seconds: int = 30
    auto_create_db: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
