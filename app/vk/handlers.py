import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy.exc import IntegrityError

from app.db.models import RecurrenceType, TaskPriority
from app.db.repositories.categories import CategoryRepository
from app.db.repositories.reminders import ReminderRepository
from app.db.repositories.tasks import TaskRepository
from app.db.repositories.users import UserRepository
from app.db.session import async_session_maker
from app.schemas.categories import CategoryCreate
from app.schemas.reminders import ReminderCreate
from app.schemas.tasks import TaskCreate
from app.services.datetime_parser import format_datetime, parse_user_datetime
from app.vk.client import VkClient
from app.vk.keyboards import (
    back_to_menu,
    categories_menu,
    main_menu,
    priority_select,
    recurrence_select,
    reminder_category_select,
    reminders_menu,
    tasks_menu,
)


@dataclass
class VkState:
    name: str | None = None
    data: dict[str, Any] = field(default_factory=dict)


class VkStateStore:
    def __init__(self) -> None:
        self._states: dict[int, VkState] = {}

    def get(self, vk_user_id: int) -> VkState:
        return self._states.setdefault(vk_user_id, VkState())

    def clear(self, vk_user_id: int) -> None:
        self._states.pop(vk_user_id, None)


RECURRENCE_LABELS = {
    RecurrenceType.ONCE: "разовое",
    RecurrenceType.DAILY: "каждый день",
    RecurrenceType.WEEKLY: "каждую неделю",
    RecurrenceType.MONTHLY: "каждый месяц",
    RecurrenceType.YEARLY: "каждый год",
}

PRIORITY_LABELS = {
    TaskPriority.LOW: "низкий",
    TaskPriority.NORMAL: "обычный",
    TaskPriority.HIGH: "высокий",
}


class VkBotHandler:
    def __init__(self, client: VkClient) -> None:
        self.client = client
        self.states = VkStateStore()

    async def handle_message(self, message: dict[str, Any]) -> None:
        vk_user_id = message["from_id"]
        peer_id = message["peer_id"]
        text = (message.get("text") or "").strip()
        cmd = self._extract_command(message, text)

        if cmd == "main:menu" or text.lower() in {"/start", "start", "начать", "меню"}:
            self.states.clear(vk_user_id)
            await self._ensure_user(vk_user_id)
            await self._send(peer_id, "Главное меню", main_menu())
            return

        state = self.states.get(vk_user_id)
        if state.name:
            handled = await self._handle_state(vk_user_id, peer_id, text, cmd, state)
            if handled:
                return

        await self._handle_command(vk_user_id, peer_id, cmd)

    def _extract_command(self, message: dict[str, Any], text: str) -> str:
        payload = message.get("payload")
        if payload:
            try:
                data = json.loads(payload)
                if isinstance(data, dict) and isinstance(data.get("cmd"), str):
                    return data["cmd"]
            except json.JSONDecodeError:
                pass

        labels = {
            "dashboard": "main:dashboard",
            "напоминания": "main:reminders",
            "задачи": "main:tasks",
            "категории": "main:categories",
            "назад": "main:menu",
            "добавить": "add",
        }
        return labels.get(text.lower(), text)

    async def _ensure_user(self, vk_user_id: int) -> int:
        first_name = None
        last_name = None
        try:
            profile = await self.client.users_get(vk_user_id)
        except Exception:
            profile = None

        if profile:
            first_name = profile.get("first_name")
            last_name = profile.get("last_name")

        async with async_session_maker() as session:
            user = await UserRepository(session).get_or_create_from_vk(
                vk_user_id=vk_user_id,
                first_name=first_name,
                last_name=last_name,
            )
            await session.commit()
            return user.id

    async def _send(self, peer_id: int, text: str, keyboard: dict[str, Any] | None = None) -> None:
        await self.client.send_message(peer_id=peer_id, message=text, keyboard=keyboard)

    async def _handle_command(self, vk_user_id: int, peer_id: int, cmd: str) -> None:
        if cmd == "main:dashboard":
            await self._dashboard(vk_user_id, peer_id)
        elif cmd == "main:categories":
            await self._categories(vk_user_id, peer_id)
        elif cmd == "cat:add":
            state = self.states.get(vk_user_id)
            state.name = "category:title"
            state.data = {}
            await self._send(peer_id, "Введите название категории.", back_to_menu())
        elif cmd.startswith("cat:delete:"):
            await self._delete_category(vk_user_id, peer_id, int(cmd.rsplit(":", 1)[1]))
        elif cmd == "main:reminders":
            await self._reminders(vk_user_id, peer_id)
        elif cmd == "rem:add":
            state = self.states.get(vk_user_id)
            state.name = "reminder:title"
            state.data = {}
            await self._send(peer_id, "Введите заголовок напоминания.", back_to_menu())
        elif cmd.startswith("rem:disable:"):
            await self._disable_reminder(vk_user_id, peer_id, int(cmd.rsplit(":", 1)[1]))
        elif cmd == "main:tasks":
            await self._tasks(vk_user_id, peer_id)
        elif cmd == "task:add":
            state = self.states.get(vk_user_id)
            state.name = "task:title"
            state.data = {}
            await self._send(peer_id, "Введите заголовок задачи.", back_to_menu())
        elif cmd.startswith("task:done:"):
            await self._complete_task(vk_user_id, peer_id, int(cmd.rsplit(":", 1)[1]))
        else:
            await self._send(peer_id, "Не понял команду. Откройте главное меню.", main_menu())

    async def _handle_state(
        self,
        vk_user_id: int,
        peer_id: int,
        text: str,
        cmd: str,
        state: VkState,
    ) -> bool:
        if cmd == "main:menu":
            self.states.clear(vk_user_id)
            await self._send(peer_id, "Главное меню", main_menu())
            return True

        if state.name == "category:title":
            await self._save_category(vk_user_id, peer_id, text)
            return True

        if state.name == "reminder:title":
            if len(text) < 2:
                await self._send(peer_id, "Заголовок должен быть длиннее одного символа.", back_to_menu())
                return True
            state.data["title"] = text
            state.name = "reminder:description"
            await self._send(peer_id, "Введите описание или отправьте `-`, чтобы пропустить.")
            return True

        if state.name == "reminder:description":
            state.data["description"] = None if text == "-" else text
            state.name = "reminder:category"
            await self._ask_reminder_category(vk_user_id, peer_id)
            return True

        if state.name == "reminder:category" and cmd.startswith("rem:category:"):
            raw_category_id = cmd.rsplit(":", 1)[1]
            state.data["category_id"] = None if raw_category_id == "none" else int(raw_category_id)
            state.name = "reminder:recurrence"
            await self._send(peer_id, "Выберите тип повтора.", recurrence_select())
            return True

        if state.name == "reminder:recurrence" and cmd.startswith("rem:recurrence:"):
            state.data["recurrence"] = cmd.rsplit(":", 1)[1]
            state.name = "reminder:remind_at"
            await self._send(peer_id, "Введите дату и время: ДД.ММ.ГГГГ ЧЧ:ММ или ДД.ММ ЧЧ:ММ.", back_to_menu())
            return True

        if state.name == "reminder:remind_at":
            await self._save_reminder(vk_user_id, peer_id, text, state)
            return True

        if state.name == "task:title":
            if len(text) < 2:
                await self._send(peer_id, "Заголовок должен быть длиннее одного символа.", back_to_menu())
                return True
            state.data["title"] = text
            state.name = "task:description"
            await self._send(peer_id, "Введите описание или отправьте `-`, чтобы пропустить.")
            return True

        if state.name == "task:description":
            state.data["description"] = None if text == "-" else text
            state.name = "task:due_at"
            await self._send(peer_id, "Введите дедлайн ДД.ММ.ГГГГ ЧЧ:ММ, ДД.ММ ЧЧ:ММ или `-` без срока.")
            return True

        if state.name == "task:due_at":
            if text == "-":
                state.data["due_at"] = None
            else:
                try:
                    state.data["due_at"] = parse_user_datetime(text)
                except ValueError:
                    await self._send(peer_id, "Не понял дату. Пример: 15.06.2026 09:30")
                    return True
            state.name = "task:priority"
            await self._send(peer_id, "Выберите приоритет.", priority_select())
            return True

        if state.name == "task:priority" and cmd.startswith("task:priority:"):
            await self._save_task(vk_user_id, peer_id, TaskPriority(cmd.rsplit(":", 1)[1]), state)
            return True

        return False

    async def _dashboard(self, vk_user_id: int, peer_id: int) -> None:
        async with async_session_maker() as session:
            user_id = await self._get_user_id(session, vk_user_id)
            counts = await TaskRepository(session).dashboard_counts(user_id, datetime.now())
            upcoming = await ReminderRepository(session).upcoming_for_user(user_id, limit=5)
            await session.commit()

        reminder_lines = "\n".join(
            f"#{item.id} {format_datetime(item.next_run_at)} - {item.title}" for item in upcoming
        )
        if not reminder_lines:
            reminder_lines = "Ближайших напоминаний нет."

        await self._send(
            peer_id,
            "Dashboard\n\n"
            f"Задач активно: {counts['active']}\n"
            f"На сегодня: {counts['today']}\n"
            f"Просрочено: {counts['overdue']}\n\n"
            f"Ближайшие напоминания:\n{reminder_lines}",
            back_to_menu(),
        )

    async def _categories(self, vk_user_id: int, peer_id: int) -> None:
        async with async_session_maker() as session:
            user_id = await self._get_user_id(session, vk_user_id)
            items = await CategoryRepository(session).list_for_user(user_id)
            await session.commit()

        lines = "\n".join(f"- {item.title}" for item in items) or "Категорий пока нет."
        await self._send(peer_id, f"Категории:\n\n{lines}", categories_menu(items))

    async def _save_category(self, vk_user_id: int, peer_id: int, title: str) -> None:
        if len(title) < 2:
            await self._send(peer_id, "Название должно быть длиннее одного символа.", back_to_menu())
            return

        async with async_session_maker() as session:
            user_id = await self._get_user_id(session, vk_user_id)
            try:
                await CategoryRepository(session).create(user_id, CategoryCreate(title=title))
                await session.commit()
            except IntegrityError:
                await session.rollback()
                await self._send(peer_id, "Такая категория уже есть.", back_to_menu())
                return

        self.states.clear(vk_user_id)
        await self._send(peer_id, "Категория создана.", back_to_menu())

    async def _delete_category(self, vk_user_id: int, peer_id: int, category_id: int) -> None:
        async with async_session_maker() as session:
            user_id = await self._get_user_id(session, vk_user_id)
            deleted = await CategoryRepository(session).delete(user_id, category_id)
            await session.commit()
        await self._send(peer_id, "Категория удалена." if deleted else "Категория не найдена.", back_to_menu())

    async def _reminders(self, vk_user_id: int, peer_id: int) -> None:
        async with async_session_maker() as session:
            user_id = await self._get_user_id(session, vk_user_id)
            items = await ReminderRepository(session).list_active_for_user(user_id)
            await session.commit()

        if not items:
            text = "Активных напоминаний пока нет."
        else:
            lines = []
            for item in items:
                category = item.category.title if item.category else "без категории"
                lines.append(
                    f"#{item.id} {format_datetime(item.next_run_at)}\n"
                    f"{item.title}\n"
                    f"Категория: {category}; повтор: {RECURRENCE_LABELS[item.recurrence]}"
                )
            text = "Активные напоминания:\n\n" + "\n\n".join(lines)
        await self._send(peer_id, text, reminders_menu([item.id for item in items]))

    async def _ask_reminder_category(self, vk_user_id: int, peer_id: int) -> None:
        async with async_session_maker() as session:
            user_id = await self._get_user_id(session, vk_user_id)
            categories = await CategoryRepository(session).list_for_user(user_id)
            await session.commit()
        await self._send(peer_id, "Выберите категорию.", reminder_category_select(categories))

    async def _save_reminder(self, vk_user_id: int, peer_id: int, text: str, state: VkState) -> None:
        try:
            remind_at = parse_user_datetime(text)
        except ValueError:
            await self._send(peer_id, "Не понял дату. Пример: 15.06.2026 09:30")
            return

        if remind_at <= datetime.now():
            await self._send(peer_id, "Дата напоминания должна быть в будущем.")
            return

        async with async_session_maker() as session:
            user_id = await self._get_user_id(session, vk_user_id)
            await ReminderRepository(session).create(
                user_id=user_id,
                data=ReminderCreate(
                    category_id=state.data["category_id"],
                    title=state.data["title"],
                    description=state.data["description"],
                    remind_at=remind_at,
                    recurrence=RecurrenceType(state.data["recurrence"]),
                ),
            )
            await session.commit()

        self.states.clear(vk_user_id)
        await self._send(peer_id, "Напоминание создано.", back_to_menu())

    async def _disable_reminder(self, vk_user_id: int, peer_id: int, reminder_id: int) -> None:
        async with async_session_maker() as session:
            user_id = await self._get_user_id(session, vk_user_id)
            disabled = await ReminderRepository(session).deactivate(user_id, reminder_id)
            await session.commit()
        await self._send(peer_id, "Напоминание отключено." if disabled else "Напоминание не найдено.", back_to_menu())

    async def _tasks(self, vk_user_id: int, peer_id: int) -> None:
        async with async_session_maker() as session:
            user_id = await self._get_user_id(session, vk_user_id)
            items = await TaskRepository(session).active_for_user(user_id)
            await session.commit()

        if not items:
            text = "Активных задач пока нет."
        else:
            lines = [
                f"#{item.id} {item.title}\n"
                f"Срок: {format_datetime(item.due_at)}; приоритет: {PRIORITY_LABELS[item.priority]}"
                for item in items
            ]
            text = "Активные задачи:\n\n" + "\n\n".join(lines)
        await self._send(peer_id, text, tasks_menu([item.id for item in items]))

    async def _save_task(self, vk_user_id: int, peer_id: int, priority: TaskPriority, state: VkState) -> None:
        async with async_session_maker() as session:
            user_id = await self._get_user_id(session, vk_user_id)
            await TaskRepository(session).create(
                user_id=user_id,
                data=TaskCreate(
                    title=state.data["title"],
                    description=state.data["description"],
                    due_at=state.data["due_at"],
                    priority=priority,
                ),
            )
            await session.commit()

        self.states.clear(vk_user_id)
        await self._send(peer_id, "Задача создана.", back_to_menu())

    async def _complete_task(self, vk_user_id: int, peer_id: int, task_id: int) -> None:
        async with async_session_maker() as session:
            user_id = await self._get_user_id(session, vk_user_id)
            completed = await TaskRepository(session).complete(user_id, task_id)
            await session.commit()
        await self._send(peer_id, "Задача закрыта." if completed else "Задача не найдена.", back_to_menu())

    async def _get_user_id(self, session, vk_user_id: int) -> int:
        user = await UserRepository(session).get_or_create_from_vk(vk_user_id=vk_user_id)
        return user.id
