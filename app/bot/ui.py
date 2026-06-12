from html import escape

from app.services.datetime_parser import format_datetime


def h(value: object) -> str:
    return escape(str(value), quote=False)


def header(title: str, subtitle: str | None = None) -> str:
    if subtitle:
        return f"<b>{h(title)}</b>\n{h(subtitle)}"
    return f"<b>{h(title)}</b>"


def empty_state(title: str, hint: str) -> str:
    return f"<b>{h(title)}</b>\n\n{h(hint)}"


def field(label: str, value: object | None) -> str:
    display_value = value if value not in (None, "") else "не указано"
    return f"<b>{h(label)}:</b> {h(display_value)}"


def date_field(label: str, value) -> str:
    return field(label, format_datetime(value))
