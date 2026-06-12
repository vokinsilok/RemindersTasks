from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.bot.handlers.common import ensure_user
from app.bot.keyboards.common import back_to_menu, priority_select, tasks_menu
from app.db.models import TaskPriority
from app.db.repositories.tasks import TaskRepository
from app.db.session import async_session_maker
from app.schemas.tasks import TaskCreate
from app.services.datetime_parser import format_datetime, parse_user_datetime

router = Router()


class TaskStates(StatesGroup):
    title = State()
    description = State()
    due_at = State()
    priority = State()


PRIORITY_LABELS = {
    TaskPriority.LOW: "низкий",
    TaskPriority.NORMAL: "обычный",
    TaskPriority.HIGH: "высокий",
}


def render_tasks_text(items) -> str:
    if not items:
        return "Активных задач пока нет."

    lines = []
    for item in items:
        lines.append(
            f"#{item.id} {item.title}\n"
            f"Срок: {format_datetime(item.due_at)}; приоритет: {PRIORITY_LABELS[item.priority]}"
        )
    return "Активные задачи:\n\n" + "\n\n".join(lines)


@router.callback_query(F.data == "main:tasks")
async def tasks(callback: CallbackQuery) -> None:
    async with async_session_maker() as session:
        user_id = await ensure_user(session, callback.from_user)
        items = await TaskRepository(session).active_for_user(user_id)
        await session.commit()

    await callback.message.edit_text(
        render_tasks_text(items),
        reply_markup=tasks_menu([item.id for item in items]),
    )
    await callback.answer()


@router.callback_query(F.data == "task:add")
async def add_task(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(TaskStates.title)
    await callback.message.edit_text("Введите заголовок задачи.", reply_markup=back_to_menu())
    await callback.answer()


@router.message(TaskStates.title)
async def task_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if len(title) < 2:
        await message.answer("Заголовок должен быть длиннее одного символа.")
        return

    await state.update_data(title=title)
    await state.set_state(TaskStates.description)
    await message.answer("Введите описание или отправьте `-`, чтобы пропустить.")


@router.message(TaskStates.description)
async def task_description(message: Message, state: FSMContext) -> None:
    description = (message.text or "").strip()
    await state.update_data(description=None if description == "-" else description)
    await state.set_state(TaskStates.due_at)
    await message.answer(
        "Введите дедлайн `ДД.ММ.ГГГГ ЧЧ:ММ`, `ДД.ММ ЧЧ:ММ` или `-` без срока.",
        parse_mode="Markdown",
    )


@router.message(TaskStates.due_at)
async def task_due_at(message: Message, state: FSMContext) -> None:
    raw_due_at = (message.text or "").strip()
    if raw_due_at == "-":
        due_at = None
    else:
        try:
            due_at = parse_user_datetime(raw_due_at)
        except ValueError:
            await message.answer("Не понял дату. Пример: `15.06.2026 09:30`.", parse_mode="Markdown")
            return

    await state.update_data(due_at=due_at)
    await state.set_state(TaskStates.priority)
    await message.answer("Выберите приоритет.", reply_markup=priority_select())


@router.callback_query(TaskStates.priority, F.data.startswith("task:priority:"))
async def task_priority(callback: CallbackQuery, state: FSMContext) -> None:
    priority = TaskPriority(callback.data.rsplit(":", 1)[1])
    data = await state.get_data()

    async with async_session_maker() as session:
        user_id = await ensure_user(session, callback.from_user)
        await TaskRepository(session).create(
            user_id=user_id,
            data=TaskCreate(
                title=data["title"],
                description=data["description"],
                due_at=data["due_at"],
                priority=priority,
            ),
        )
        await session.commit()

    await state.clear()
    await callback.message.edit_text("Задача создана.", reply_markup=back_to_menu())
    await callback.answer()


@router.callback_query(F.data.startswith("task:done:"))
async def complete_task(callback: CallbackQuery) -> None:
    task_id = int(callback.data.rsplit(":", 1)[1])
    async with async_session_maker() as session:
        user_id = await ensure_user(session, callback.from_user)
        completed = await TaskRepository(session).complete(user_id, task_id)
        await session.commit()

    await callback.answer("Задача закрыта." if completed else "Задача не найдена.")
    await tasks(callback)
