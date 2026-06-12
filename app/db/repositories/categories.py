from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Reminder, ReminderCategory
from app.schemas.categories import CategoryCreate


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_user(self, user_id: int) -> list[ReminderCategory]:
        result = await self.session.execute(
            select(ReminderCategory)
            .where(ReminderCategory.user_id == user_id)
            .order_by(ReminderCategory.title)
        )
        return list(result.scalars())

    async def get(self, user_id: int, category_id: int) -> ReminderCategory | None:
        result = await self.session.execute(
            select(ReminderCategory).where(
                ReminderCategory.user_id == user_id,
                ReminderCategory.id == category_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: int, data: CategoryCreate) -> ReminderCategory:
        category = ReminderCategory(user_id=user_id, title=data.title.strip())
        self.session.add(category)
        await self.session.flush()
        return category

    async def delete(self, user_id: int, category_id: int) -> bool:
        category = await self.get(user_id, category_id)
        if category is None:
            return False

        await self.session.execute(
            update(Reminder)
            .where(Reminder.user_id == user_id, Reminder.category_id == category_id)
            .values(category_id=None)
        )
        await self.session.execute(
            delete(ReminderCategory).where(
                ReminderCategory.user_id == user_id,
                ReminderCategory.id == category_id,
            )
        )
        await self.session.flush()
        return True
