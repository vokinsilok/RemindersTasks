from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import IntegrityError

from app.bot.handlers.common import ensure_user
from app.bot.keyboards.common import back_to_menu, categories_menu
from app.db.repositories.categories import CategoryRepository
from app.db.session import async_session_maker
from app.schemas.categories import CategoryCreate

router = Router()


class CategoryStates(StatesGroup):
    title = State()


def render_categories_text(category_titles: list[str]) -> str:
    if not category_titles:
        return "Категорий пока нет."
    lines = "\n".join(f"- {title}" for title in category_titles)
    return f"Категории:\n\n{lines}"


@router.callback_query(F.data == "main:categories")
async def categories(callback: CallbackQuery) -> None:
    async with async_session_maker() as session:
        user_id = await ensure_user(session, callback.from_user)
        category_repo = CategoryRepository(session)
        items = await category_repo.list_for_user(user_id)
        await session.commit()

    await callback.message.edit_text(
        render_categories_text([item.title for item in items]),
        reply_markup=categories_menu(items),
    )
    await callback.answer()


@router.callback_query(F.data == "cat:add")
async def add_category(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CategoryStates.title)
    await callback.message.edit_text(
        "Введите название категории.",
        reply_markup=back_to_menu(),
    )
    await callback.answer()


@router.message(CategoryStates.title)
async def save_category(message: Message, state: FSMContext) -> None:
    title = message.text.strip()
    if len(title) < 2:
        await message.answer("Название должно быть длиннее одного символа.")
        return

    async with async_session_maker() as session:
        user_id = await ensure_user(session, message.from_user)
        category_repo = CategoryRepository(session)
        try:
            await category_repo.create(user_id, CategoryCreate(title=title))
            await session.commit()
        except IntegrityError:
            await session.rollback()
            await message.answer("Такая категория уже есть.", reply_markup=back_to_menu())
            return

    await state.clear()
    await message.answer("Категория создана.", reply_markup=back_to_menu())


@router.callback_query(F.data.startswith("cat:delete:"))
async def delete_category(callback: CallbackQuery) -> None:
    category_id = int(callback.data.rsplit(":", 1)[1])
    async with async_session_maker() as session:
        user_id = await ensure_user(session, callback.from_user)
        deleted = await CategoryRepository(session).delete(user_id, category_id)
        await session.commit()

    await callback.answer("Категория удалена." if deleted else "Категория не найдена.")
    await categories(callback)
