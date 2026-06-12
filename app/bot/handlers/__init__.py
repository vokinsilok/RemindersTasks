from aiogram import Router

from app.bot.handlers.categories import router as categories_router
from app.bot.handlers.common import router as common_router
from app.bot.handlers.reminders import router as reminders_router
from app.bot.handlers.tasks import router as tasks_router


def build_router() -> Router:
    router = Router()
    router.include_router(common_router)
    router.include_router(categories_router)
    router.include_router(reminders_router)
    router.include_router(tasks_router)
    return router
