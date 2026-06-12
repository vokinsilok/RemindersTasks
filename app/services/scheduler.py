import asyncio
import logging
from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from app.config import get_settings
from app.db.models import RecurrenceType, Reminder
from app.db.repositories.reminders import ReminderRepository
from app.db.session import async_session_maker
from app.services.datetime_parser import format_datetime
from app.services.recurrence import calculate_next_run

logger = logging.getLogger(__name__)


def build_reminder_message(reminder: Reminder) -> str:
    category = reminder.category.title if reminder.category else "без категории"
    parts = [
        "Напоминание",
        "",
        reminder.title,
        f"Категория: {category}",
        f"Время: {format_datetime(reminder.next_run_at)}",
    ]
    if reminder.description:
        parts.extend(["", reminder.description])
    return "\n".join(parts)


def calculate_future_next_run(reminder: Reminder, now: datetime) -> datetime | None:
    next_run = calculate_next_run(reminder.next_run_at, reminder.recurrence)
    while next_run is not None and next_run <= now:
        next_run = calculate_next_run(next_run, reminder.recurrence)
    return next_run


async def process_due_reminders(bot: Bot) -> None:
    now = datetime.now()
    async with async_session_maker() as session:
        repo = ReminderRepository(session)
        due_reminders = await repo.due(now)

        for reminder in due_reminders:
            try:
                await bot.send_message(
                    reminder.user.telegram_id,
                    build_reminder_message(reminder),
                )
            except (TelegramForbiddenError, TelegramBadRequest) as exc:
                logger.warning("Failed to send reminder %s: %s", reminder.id, exc)
                continue

            if reminder.recurrence == RecurrenceType.ONCE:
                reminder.is_active = False
            else:
                reminder.next_run_at = calculate_future_next_run(reminder, now)
                if reminder.next_run_at is None:
                    reminder.is_active = False

        await session.commit()


async def run_scheduler(bot: Bot) -> None:
    settings = get_settings()
    while True:
        try:
            await process_due_reminders(bot)
        except Exception:
            logger.exception("Scheduler iteration failed")
        await asyncio.sleep(settings.scheduler_poll_seconds)
