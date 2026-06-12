import json
from typing import Any

from app.db.models import RecurrenceType, ReminderCategory, TaskPriority


def button(label: str, cmd: str, color: str = "secondary") -> dict[str, Any]:
    return {
        "action": {
            "type": "text",
            "label": label,
            "payload": json.dumps({"cmd": cmd}, ensure_ascii=False),
        },
        "color": color,
    }


def keyboard(rows: list[list[dict[str, Any]]]) -> dict[str, Any]:
    return {
        "one_time": False,
        "inline": False,
        "buttons": rows,
    }


def main_menu() -> dict[str, Any]:
    return keyboard(
        [
            [button("Dashboard", "main:dashboard", "primary")],
            [button("Напоминания", "main:reminders"), button("Задачи", "main:tasks")],
            [button("Категории", "main:categories")],
        ]
    )


def back_to_menu() -> dict[str, Any]:
    return keyboard([[button("Назад", "main:menu", "primary")]])


def categories_menu(categories: list[ReminderCategory]) -> dict[str, Any]:
    rows = [[button("Добавить", "cat:add", "positive")]]
    rows.extend([[button(f"Удалить: {category.title}", f"cat:delete:{category.id}", "negative")] for category in categories[:8]])
    rows.append([button("Назад", "main:menu", "primary")])
    return keyboard(rows)


def reminder_category_select(categories: list[ReminderCategory]) -> dict[str, Any]:
    rows = [[button("Без категории", "rem:category:none", "primary")]]
    rows.extend([[button(category.title, f"rem:category:{category.id}")] for category in categories[:8]])
    rows.append([button("Отмена", "main:menu", "negative")])
    return keyboard(rows)


def recurrence_select() -> dict[str, Any]:
    labels = {
        RecurrenceType.ONCE: "Разовое",
        RecurrenceType.DAILY: "Каждый день",
        RecurrenceType.WEEKLY: "Каждую неделю",
        RecurrenceType.MONTHLY: "Каждый месяц",
        RecurrenceType.YEARLY: "Каждый год",
    }
    return keyboard([[button(label, f"rem:recurrence:{value.value}")] for value, label in labels.items()])


def reminders_menu(reminder_ids: list[int]) -> dict[str, Any]:
    rows = [[button("Добавить", "rem:add", "positive")]]
    rows.extend([[button(f"Отключить #{reminder_id}", f"rem:disable:{reminder_id}", "negative")] for reminder_id in reminder_ids[:8]])
    rows.append([button("Назад", "main:menu", "primary")])
    return keyboard(rows)


def priority_select() -> dict[str, Any]:
    labels = {
        TaskPriority.LOW: "Низкий",
        TaskPriority.NORMAL: "Обычный",
        TaskPriority.HIGH: "Высокий",
    }
    return keyboard([[button(label, f"task:priority:{value.value}")] for value, label in labels.items()])


def tasks_menu(task_ids: list[int]) -> dict[str, Any]:
    rows = [[button("Добавить", "task:add", "positive")]]
    rows.extend([[button(f"Готово #{task_id}", f"task:done:{task_id}", "positive")] for task_id in task_ids[:8]])
    rows.append([button("Назад", "main:menu", "primary")])
    return keyboard(rows)
