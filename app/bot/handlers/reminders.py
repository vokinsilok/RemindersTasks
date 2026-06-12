from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.bot.handlers.common import ensure_user
from app.bot.keyboards.common import (
    back_to_menu,
    recurrence_select,
    reminder_category_select,
    reminders_menu,
)
from app.bot.ui import empty_state, field, h, header
from app.db.models import RecurrenceType
from app.db.repositories.categories import CategoryRepository
from app.db.repositories.reminders import ReminderRepository
from app.db.session import async_session_maker
from app.schemas.reminders import ReminderCreate
from app.services.datetime_parser import format_datetime, parse_user_datetime

router = Router()


class ReminderStates(StatesGroup):
    title = State()
    description = State()
    category = State()
    recurrence = State()
    remind_at = State()


RECURRENCE_LABELS = {
    RecurrenceType.ONCE: "один раз",
    RecurrenceType.DAILY: "каждый день",
    RecurrenceType.WEEKLY: "каждую неделю",
    RecurrenceType.MONTHLY: "каждый месяц",
    RecurrenceType.YEARLY: "каждый год",
}


def render_reminders_text(items) -> str:
    if not items:
        return empty_state(
            "Напоминания",
            "Активных напоминаний пока нет. Создайте первое и бот напишет в нужное время.",
        )

    blocks = []
    for item in items:
        category = item.category.title if item.category else "без категории"
        description = f"\n{h(item.description)}" if item.description else ""
        blocks.append(
            f"<b>#{item.id} {h(item.title)}</b>{description}\n"
            f"{field('Когда', format_datetime(item.next_run_at))}\n"
            f"{field('Категория', category)}\n"
            f"{field('Повтор', RECURRENCE_LABELS[item.recurrence])}"
        )
    return f"{header('Напоминания', 'Активные уведомления в порядке ближайшего срока.')}\n\n" + "\n\n".join(blocks)


@router.callback_query(F.data == "main:reminders")
async def reminders(callback: CallbackQuery) -> None:
    async with async_session_maker() as session:
        user_id = await ensure_user(session, callback.from_user)
        items = await ReminderRepository(session).list_active_for_user(user_id)
        await session.commit()

    await callback.message.edit_text(
        render_reminders_text(items),
        reply_markup=reminders_menu([item.id for item in items]),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "rem:add")
async def add_reminder(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ReminderStates.title)
    await callback.message.edit_text(
        f"{header('Новое напоминание', 'Шаг 1 из 5 - заголовок.')}\n\n"
        "Напишите короткое название. Например: Оплатить интернет.",
        reply_markup=back_to_menu(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(ReminderStates.title)
async def reminder_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if len(title) < 2:
        await message.answer("Заголовок должен быть длиннее одного символа.")
        return

    await state.update_data(title=title)
    await state.set_state(ReminderStates.description)
    await message.answer(
        f"{header('Новое напоминание', 'Шаг 2 из 5 - описание.')}\n\n"
        "Добавьте детали или отправьте '-', если описание не нужно.",
        parse_mode="HTML",
    )


@router.message(ReminderStates.description)
async def reminder_description(message: Message, state: FSMContext) -> None:
    description = (message.text or "").strip()
    await state.update_data(description=None if description == "-" else description)
    await state.set_state(ReminderStates.category)

    async with async_session_maker() as session:
        user_id = await ensure_user(session, message.from_user)
        categories = await CategoryRepository(session).list_for_user(user_id)
        await session.commit()

    await message.answer(
        f"{header('Новое напоминание', 'Шаг 3 из 5 - категория.')}\n\n"
        "Выберите категорию или оставьте напоминание без категории.",
        reply_markup=reminder_category_select(categories),
        parse_mode="HTML",
    )


@router.callback_query(ReminderStates.category, F.data.startswith("rem:category:"))
async def reminder_category(callback: CallbackQuery, state: FSMContext) -> None:
    raw_category_id = callback.data.rsplit(":", 1)[1]
    category_id = None if raw_category_id == "none" else int(raw_category_id)
    await state.update_data(category_id=category_id)
    await state.set_state(ReminderStates.recurrence)
    await callback.message.edit_text(
        f"{header('Новое напоминание', 'Шаг 4 из 5 - повтор.')}\n\n"
        "Выберите, как часто напоминание должно срабатывать.",
        reply_markup=recurrence_select(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(ReminderStates.recurrence, F.data.startswith("rem:recurrence:"))
async def reminder_recurrence(callback: CallbackQuery, state: FSMContext) -> None:
    recurrence = RecurrenceType(callback.data.rsplit(":", 1)[1])
    await state.update_data(recurrence=recurrence.value)
    await state.set_state(ReminderStates.remind_at)
    await callback.message.edit_text(
        f"{header('Новое напоминание', 'Шаг 5 из 5 - дата и время.')}\n\n"
        "Формат: ДД.ММ.ГГГГ ЧЧ:ММ\n"
        "Можно короче: ДД.ММ ЧЧ:ММ\n\n"
        "Пример: 15.06.2026 09:30",
        reply_markup=back_to_menu(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(ReminderStates.remind_at)
async def reminder_remind_at(message: Message, state: FSMContext) -> None:
    try:
        remind_at = parse_user_datetime(message.text or "")
    except ValueError:
        await message.answer("Не понял дату. Пример: 15.06.2026 09:30")
        return

    if remind_at <= datetime.now():
        await message.answer("Дата напоминания должна быть в будущем.")
        return

    data = await state.get_data()
    async with async_session_maker() as session:
        user_id = await ensure_user(session, message.from_user)
        await ReminderRepository(session).create(
            user_id=user_id,
            data=ReminderCreate(
                category_id=data["category_id"],
                title=data["title"],
                description=data["description"],
                remind_at=remind_at,
                recurrence=RecurrenceType(data["recurrence"]),
            ),
        )
        await session.commit()

    await state.clear()
    await message.answer(
        f"{header('Напоминание создано')}\n\n"
        f"{field('Название', data['title'])}\n"
        f"{field('Когда', format_datetime(remind_at))}\n"
        f"{field('Повтор', RECURRENCE_LABELS[RecurrenceType(data['recurrence'])])}",
        reply_markup=back_to_menu(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("rem:disable:"))
async def disable_reminder(callback: CallbackQuery) -> None:
    reminder_id = int(callback.data.rsplit(":", 1)[1])
    async with async_session_maker() as session:
        user_id = await ensure_user(session, callback.from_user)
        disabled = await ReminderRepository(session).deactivate(user_id, reminder_id)
        await session.commit()

    await callback.answer("Напоминание отключено." if disabled else "Напоминание не найдено.")
    await reminders(callback)
