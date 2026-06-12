from aiogram.types import User as TelegramUser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def get_by_vk_user_id(self, vk_user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.vk_user_id == vk_user_id))
        return result.scalar_one_or_none()

    async def get_or_create_from_telegram(self, telegram_user: TelegramUser) -> User:
        user = await self.get_by_telegram_id(telegram_user.id)
        if user is None:
            user = User(
                platform="telegram",
                telegram_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
            )
            self.session.add(user)
            await self.session.flush()
            return user

        user.username = telegram_user.username
        user.first_name = telegram_user.first_name
        user.last_name = telegram_user.last_name
        await self.session.flush()
        return user

    async def get_or_create_from_vk(
        self,
        *,
        vk_user_id: int,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> User:
        user = await self.get_by_vk_user_id(vk_user_id)
        if user is None:
            user = User(
                platform="vk",
                vk_user_id=vk_user_id,
                first_name=first_name,
                last_name=last_name,
            )
            self.session.add(user)
            await self.session.flush()
            return user

        user.first_name = first_name or user.first_name
        user.last_name = last_name or user.last_name
        await self.session.flush()
        return user
