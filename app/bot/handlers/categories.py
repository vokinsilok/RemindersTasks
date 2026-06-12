from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import IntegrityError

from app.bot.handlers.common import ensure_user
from app.bot.keyboards.common import back_to_menu, categories_menu
from app.bot.ui import empty_state, h, header
from app.db.repositories.categories import CategoryRepository
from app.db.session import async_session_maker
from app.schemas.categories import CategoryCreate

router = Router()


class CategoryStates(StatesGroup):
    title = State()


def render_categories_text(items) -> str:
    if not items:
        return empty_state(
            "Категории",
            "Категорий пока нет. Создайте первую, например: Работа, Семья, Здоровье.",
        )

    lines = "\n".join(f"#{item.id} - <b>{h(item.title)}</b>" for item in items)
    return f"{header('Категории', 'Группируйте напоминания так, как удобно вам.')}\n\n{lines}"


@router.callback_query(F.data == "main:categories")
async def categories(callback: CallbackQuery) -> None:
    async with async_session_maker() as session:
        user_id = await ensure_user(session, callback.from_user)
        items = await CategoryRepository(session).list_for_user(user_id)
        await session.commit()

    await callback.message.edit_text(
        render_categories_text(items),
        reply_markup=categories_menu(items),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "cat:add")
async def add_category(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CategoryStates.title)
    await callback.message.edit_text(
        f"{header('Новая категория', 'Напишите короткое название.')}\n\n"
        "Примеры: Работа, Дни рождения, Платежи.",
        reply_markup=back_to_menu(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(CategoryStates.title)
async def save_category(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if len(title) < 2:
        await message.answer("Название должно быть длиннее одного символа.")
        return

    async with async_session_maker() as session:
        user_id = await ensure_user(session, message.from_user)
        try:
            await CategoryRepository(session).create(user_id, CategoryCreate(title=title))
            await session.commit()
        except IntegrityError:
            await session.rollback()
            await message.answer("Такая категория уже есть.", reply_markup=back_to_menu())
            return

    await state.clear()
    await message.answer(
        f"{header('Категория создана')}\n\nТеперь ее можно выбрать при создании напоминания.",
        reply_markup=back_to_menu(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("cat:delete:"))
async def delete_category(callback: CallbackQuery) -> None:
    category_id = int(callback.data.rsplit(":", 1)[1])
    async with async_session_maker() as session:
        user_id = await ensure_user(session, callback.from_user)
        deleted = await CategoryRepository(session).delete(user_id, category_id)
        await session.commit()

    await callback.answer("Категория удалена." if deleted else "Категория не найдена.")
    await categories(callback)
