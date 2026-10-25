"""Pure calendar helpers for working-day calculations."""

from calendar import monthrange
from datetime import date, timedelta


def working_days(
    start: date,
    end: date,
    holidays: set[date],
    weekend: set[int],
) -> list[date]:
    """Return working dates from ``start`` through ``end``, inclusive.

    Weekday numbers use ISO convention: Monday is 1 and Sunday is 7.
    """
    if end < start:
        return []

    result: list[date] = []
    day = start
    while day <= end:
        if day.isoweekday() not in weekend and day not in holidays:
            result.append(day)
        day += timedelta(days=1)
    return result


def days_in_month_working(
    month: date,
    holidays: set[date],
    weekend: set[int],
) -> int:
    """Count working dates in the calendar month containing ``month``."""
    first_day = month.replace(day=1)
    last_day = month.replace(day=monthrange(month.year, month.month)[1])
    return len(working_days(first_day, last_day, holidays, weekend))
