from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.common import back_to_menu, main_menu
from app.db.repositories.reminders import ReminderRepository
from app.db.repositories.tasks import TaskRepository
from app.db.repositories.users import UserRepository
from app.db.session import async_session_maker
from app.services.datetime_parser import format_datetime

router = Router()


async def ensure_user(session: AsyncSession, telegram_user) -> int:
    user = await UserRepository(session).get_or_create_from_telegram(telegram_user)
    return user.id


@router.message(Command("start"))
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    async with async_session_maker() as session:
        await ensure_user(session, message.from_user)
        await session.commit()

    await message.answer(
        "Привет. Я помогу вести напоминания и задачи.",
        reply_markup=main_menu(),
    )


@router.message(Command("menu"))
async def menu_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Главное меню", reply_markup=main_menu())


@router.callback_query(F.data == "main:menu")
async def menu_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Главное меню", reply_markup=main_menu())
    await callback.answer()


@router.callback_query(F.data == "main:dashboard")
async def dashboard(callback: CallbackQuery) -> None:
    async with async_session_maker() as session:
        user_id = await ensure_user(session, callback.from_user)
        tasks = TaskRepository(session)
        reminders = ReminderRepository(session)
        counts = await tasks.dashboard_counts(user_id, datetime.now())
        upcoming = await reminders.upcoming_for_user(user_id, limit=5)
        await session.commit()

    reminder_lines = "\n".join(
        f"#{item.id} {format_datetime(item.next_run_at)} - {item.title}" for item in upcoming
    )
    if not reminder_lines:
        reminder_lines = "Ближайших напоминаний нет."

    text = (
        "Dashboard\n\n"
        f"Задач активно: {counts['active']}\n"
        f"На сегодня: {counts['today']}\n"
        f"Просрочено: {counts['overdue']}\n\n"
        "Ближайшие напоминания:\n"
        f"{reminder_lines}"
    )
    await callback.message.edit_text(text, reply_markup=back_to_menu())
    await callback.answer()
