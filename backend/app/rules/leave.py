"""Pure leave calculation helpers."""

from datetime import date


def leave_balance(quota: int | None, approved_days: int) -> int | None:
    """Return remaining leave days, or None when the quota is unlimited."""
    if quota is None:
        return None
    return quota - approved_days


def overlaps(a_start: date, a_end: date, b_start: date, b_end: date) -> bool:
    """Return whether two inclusive date ranges share at least one day."""
    return a_start <= b_end and b_start <= a_end
