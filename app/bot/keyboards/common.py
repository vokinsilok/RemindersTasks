from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.db.models import RecurrenceType, ReminderCategory, TaskPriority


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Dashboard", callback_data="main:dashboard")],
            [
                InlineKeyboardButton(text="Напоминания", callback_data="main:reminders"),
                InlineKeyboardButton(text="Задачи", callback_data="main:tasks"),
            ],
            [InlineKeyboardButton(text="Категории", callback_data="main:categories")],
        ]
    )


def back_to_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="main:menu")]]
    )


def categories_menu(categories: list[ReminderCategory]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="Добавить", callback_data="cat:add")]]
    rows.extend(
        [InlineKeyboardButton(text=f"Удалить: {category.title}", callback_data=f"cat:delete:{category.id}")]
        for category in categories
    )
    rows.append([InlineKeyboardButton(text="Назад", callback_data="main:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def reminder_category_select(categories: list[ReminderCategory]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="Без категории", callback_data="rem:category:none")]]
    rows.extend(
        [InlineKeyboardButton(text=category.title, callback_data=f"rem:category:{category.id}")]
        for category in categories
    )
    rows.append([InlineKeyboardButton(text="Отмена", callback_data="main:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def recurrence_select() -> InlineKeyboardMarkup:
    labels = {
        RecurrenceType.ONCE: "Разовое",
        RecurrenceType.DAILY: "Каждый день",
        RecurrenceType.WEEKLY: "Каждую неделю",
        RecurrenceType.MONTHLY: "Каждый месяц",
        RecurrenceType.YEARLY: "Каждый год",
    }
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"rem:recurrence:{value.value}")]
            for value, label in labels.items()
        ]
    )


def reminders_menu(reminder_ids: list[int]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="Добавить", callback_data="rem:add")]]
    rows.extend(
        [InlineKeyboardButton(text=f"Отключить #{reminder_id}", callback_data=f"rem:disable:{reminder_id}")]
        for reminder_id in reminder_ids
    )
    rows.append([InlineKeyboardButton(text="Назад", callback_data="main:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def tasks_menu(task_ids: list[int]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="Добавить", callback_data="task:add")]]
    rows.extend(
        [InlineKeyboardButton(text=f"Готово #{task_id}", callback_data=f"task:done:{task_id}")]
        for task_id in task_ids
    )
    rows.append([InlineKeyboardButton(text="Назад", callback_data="main:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def priority_select() -> InlineKeyboardMarkup:
    labels = {
        TaskPriority.LOW: "Низкий",
        TaskPriority.NORMAL: "Обычный",
        TaskPriority.HIGH: "Высокий",
    }
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"task:priority:{value.value}")]
            for value, label in labels.items()
        ]
    )
