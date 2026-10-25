"""Pure attendance status rules."""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


@dataclass
class Settings:
    office_start: time
    grace_minutes: int
    half_day_hours: float
    timezone: str
    weekend_days: set[int] = field(default_factory=lambda: {6, 7})
    late_penalty_enabled: bool = False


def _local_datetime(value: datetime, zone: ZoneInfo) -> datetime:
    """Interpret naive timestamps in the configured zone; convert aware ones."""
    if value.tzinfo is None:
        return value.replace(tzinfo=zone)
    return value.astimezone(zone)


def attendance_status(
    check_in: datetime | None,
    check_out: datetime | None,
    s: Settings,
    day_over: bool = False,
) -> str:
    """Compute the status for a stored attendance record."""
    zone = ZoneInfo(s.timezone)

    if check_in is not None and check_out is not None:
        local_in = _local_datetime(check_in, zone)
        local_out = _local_datetime(check_out, zone)
        worked_hours = (local_out - local_in).total_seconds() / 3600
        if worked_hours < s.half_day_hours:
            return "half_day"

    if check_in is not None and check_out is None and day_over:
        return "missing_checkout"

    if check_in is not None:
        local_in = _local_datetime(check_in, zone)
        grace_end = (
            datetime.combine(local_in.date(), s.office_start)
            + timedelta(minutes=s.grace_minutes)
        ).time()
        if local_in.timetz().replace(tzinfo=None) > grace_end:
            return "late"

    return "present"


def daily_status(
    day: date,
    employee_join: date,
    employee_exit: date | None,
    record,
    approved_leave: bool,
    holidays: set[date],
    s: Settings,
    today: date,
) -> str | None:
    """Return the computed daily status, or None when the date is out of scope."""
    if day.isoweekday() in s.weekend_days or day in holidays:
        return None
    if day < employee_join or (employee_exit is not None and day > employee_exit):
        return None
    if approved_leave:
        return "on_leave"
    if record is not None:
        if isinstance(record, dict):
            check_in = record.get("check_in")
            check_out = record.get("check_out")
        else:
            check_in = getattr(record, "check_in", None)
            check_out = getattr(record, "check_out", None)
        return attendance_status(check_in, check_out, s, day_over=day < today)
    if day < today:
        return "absent"
    return None
