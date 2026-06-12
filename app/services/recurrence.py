from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from app.db.models import RecurrenceType


def calculate_next_run(current: datetime, recurrence: RecurrenceType) -> datetime | None:
    if recurrence == RecurrenceType.ONCE:
        return None
    if recurrence == RecurrenceType.DAILY:
        return current + timedelta(days=1)
    if recurrence == RecurrenceType.WEEKLY:
        return current + timedelta(weeks=1)
    if recurrence == RecurrenceType.MONTHLY:
        return current + relativedelta(months=1)
    if recurrence == RecurrenceType.YEARLY:
        return current + relativedelta(years=1)
    raise ValueError(f"Unknown recurrence: {recurrence}")
