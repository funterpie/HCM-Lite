from datetime import date, datetime, time, timezone
from types import SimpleNamespace

import pytest

from app.rules.attendance import Settings, attendance_status, daily_status


@pytest.fixture
def settings():
    return Settings(
        office_start=time(9, 0),
        grace_minutes=15,
        half_day_hours=5,
        timezone="Asia/Karachi",
    )


@pytest.mark.parametrize(
    ("check_in", "expected"),
    [
        (datetime(2026, 10, 26, 9, 0), "present"),
        (datetime(2026, 10, 26, 9, 15), "present"),
        (datetime(2026, 10, 26, 9, 16), "late"),
    ],
)
def test_attendance_status_uses_local_grace_boundary(settings, check_in, expected):
    assert attendance_status(check_in, None, settings) == expected


def test_attendance_status_converts_aware_checkin_to_configured_timezone(settings):
    check_in = datetime(2026, 10, 26, 4, 16, tzinfo=timezone.utc)
    assert attendance_status(check_in, None, settings) == "late"


def test_attendance_status_short_checkout_is_half_day(settings):
    assert attendance_status(
        datetime(2026, 10, 26, 9), datetime(2026, 10, 26, 13, 59), settings
    ) == "half_day"


def test_attendance_status_five_hours_keeps_late_status(settings):
    assert attendance_status(
        datetime(2026, 10, 26, 9, 16), datetime(2026, 10, 26, 14, 16), settings
    ) == "late"


def test_attendance_status_missing_checkout_only_when_day_is_over(settings):
    check_in = datetime(2026, 10, 26, 9)
    assert attendance_status(check_in, None, settings, day_over=False) == "present"
    assert attendance_status(check_in, None, settings, day_over=True) == "missing_checkout"


def test_daily_status_non_working_weekend(settings):
    assert daily_status(
        date(2026, 10, 24), date(2026, 1, 1), None, None, False, set(), settings,
        date(2026, 10, 27),
    ) is None


def test_daily_status_holiday(settings):
    day = date(2026, 10, 26)
    assert daily_status(
        day, date(2026, 1, 1), None, None, False, {day}, settings, date(2026, 10, 27)
    ) is None


def test_daily_status_before_join_and_after_exit(settings):
    day = date(2026, 10, 26)
    assert daily_status(
        day, date(2026, 10, 27), None, None, False, set(), settings, date(2026, 10, 27)
    ) is None
    assert daily_status(
        day, date(2026, 1, 1), date(2026, 10, 25), None, False, set(), settings,
        date(2026, 10, 27),
    ) is None


def test_daily_status_approved_leave_takes_precedence(settings):
    day = date(2026, 10, 26)
    assert daily_status(
        day, date(2026, 1, 1), None, SimpleNamespace(check_in=None, check_out=None), True,
        set(), settings, date(2026, 10, 27),
    ) == "on_leave"


def test_daily_status_computes_record_status(settings):
    day = date(2026, 10, 26)
    record = SimpleNamespace(
        check_in=datetime(2026, 10, 26, 9), check_out=None, status="late"
    )
    assert daily_status(
        day, date(2026, 1, 1), None, record, False, set(), settings, date(2026, 10, 27)
    ) == "missing_checkout"


def test_daily_status_accepts_record_mapping(settings):
    day = date(2026, 10, 26)
    assert daily_status(
        day, date(2026, 1, 1), None,
        {"check_in": datetime(2026, 10, 26, 9, 16), "check_out": None},
        False, set(), settings, date(2026, 10, 26),
    ) == "late"


def test_daily_status_past_date_without_record_is_absent(settings):
    day = date(2026, 10, 26)
    assert daily_status(
        day, date(2026, 1, 1), None, None, False, set(), settings, date(2026, 10, 27)
    ) == "absent"


@pytest.mark.parametrize("day", [date(2026, 10, 26), date(2026, 10, 27)])
def test_daily_status_today_or_future_without_record_is_none(settings, day):
    assert daily_status(
        day, date(2026, 1, 1), None, None, False, set(), settings, date(2026, 10, 26)
    ) is None
