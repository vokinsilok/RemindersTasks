import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramAPIError, TelegramNetworkError
from aiogram.types import BotCommand

from app.bot.handlers import build_router
from app.config import get_settings
from app.db.session import init_db
from app.services.scheduler import run_scheduler

logger = logging.getLogger(__name__)


async def set_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="menu", description="Главное меню"),
        ]
    )


async def set_commands_with_retry(bot: Bot, attempts: int = 5) -> None:
    for attempt in range(1, attempts + 1):
        try:
            await set_commands(bot)
            return
        except (TelegramAPIError, TelegramNetworkError) as exc:
            if attempt == attempts:
                logger.warning("Failed to set bot commands after %s attempts: %s", attempts, exc)
                return

            delay = min(attempt * 2, 10)
            logger.warning(
                "Failed to set bot commands, retrying in %s seconds: %s",
                delay,
                exc,
            )
            await asyncio.sleep(delay)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = get_settings()
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is required for Telegram bot")

    if settings.auto_create_db:
        await init_db()

    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(build_router())

    scheduler_task = asyncio.create_task(run_scheduler(bot))
    try:
        await set_commands_with_retry(bot)
        await dispatcher.start_polling(bot)
    finally:
        scheduler_task.cancel()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
