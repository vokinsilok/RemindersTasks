from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import RecurrenceType, Reminder
from app.schemas.reminders import ReminderCreate


class ReminderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id: int,
        data: ReminderCreate,
    ) -> Reminder:
        reminder = Reminder(
            user_id=user_id,
            category_id=data.category_id,
            title=data.title.strip(),
            description=data.description.strip() if data.description else None,
            remind_at=data.remind_at,
            next_run_at=data.remind_at,
            recurrence=data.recurrence,
            is_active=True,
        )
        self.session.add(reminder)
        await self.session.flush()
        return reminder

    async def list_active_for_user(self, user_id: int) -> list[Reminder]:
        result = await self.session.execute(
            select(Reminder)
            .options(selectinload(Reminder.category))
            .where(Reminder.user_id == user_id, Reminder.is_active.is_(True))
            .order_by(Reminder.next_run_at)
        )
        return list(result.scalars())

    async def upcoming_for_user(self, user_id: int, limit: int = 5) -> list[Reminder]:
        result = await self.session.execute(
            select(Reminder)
            .options(selectinload(Reminder.category))
            .where(Reminder.user_id == user_id, Reminder.is_active.is_(True))
            .order_by(Reminder.next_run_at)
            .limit(limit)
        )
        return list(result.scalars())

    async def due(self, now: datetime, platform: str | None = None, limit: int = 50) -> list[Reminder]:
        conditions = [Reminder.is_active.is_(True), Reminder.next_run_at <= now]
        if platform is not None:
            conditions.append(Reminder.user.has(platform=platform))

        result = await self.session.execute(
            select(Reminder)
            .options(selectinload(Reminder.user), selectinload(Reminder.category))
            .where(*conditions)
            .order_by(Reminder.next_run_at)
            .limit(limit)
        )
        return list(result.scalars())

    async def deactivate(self, user_id: int, reminder_id: int) -> bool:
        reminder = await self.get_for_user(user_id, reminder_id)
        if reminder is None:
            return False
        reminder.is_active = False
        await self.session.flush()
        return True

    async def get_for_user(self, user_id: int, reminder_id: int) -> Reminder | None:
        result = await self.session.execute(
            select(Reminder).where(Reminder.user_id == user_id, Reminder.id == reminder_id)
        )
        return result.scalar_one_or_none()
