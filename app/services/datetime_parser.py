from datetime import datetime


DATETIME_FORMATS = ("%d.%m.%Y %H:%M", "%d.%m %H:%M")


def parse_user_datetime(value: str, now: datetime | None = None) -> datetime:
    now = now or datetime.now()
    cleaned = value.strip()

    for fmt in DATETIME_FORMATS:
        try:
            parsed = datetime.strptime(cleaned, fmt)
        except ValueError:
            continue

        if fmt == "%d.%m %H:%M":
            parsed = parsed.replace(year=now.year)
        return parsed

    raise ValueError("Unsupported datetime format")


def format_datetime(value: datetime | None) -> str:
    if value is None:
        return "без срока"
    return value.strftime("%d.%m.%Y %H:%M")
