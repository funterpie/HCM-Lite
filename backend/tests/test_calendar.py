from datetime import date

from app.rules.calendar import days_in_month_working, working_days


WEEKEND = {6, 7}


def test_normal_week_includes_monday_through_friday():
    assert working_days(date(2026, 10, 19), date(2026, 10, 25), set(), WEEKEND) == [
        date(2026, 10, 19),
        date(2026, 10, 20),
        date(2026, 10, 21),
        date(2026, 10, 22),
        date(2026, 10, 23),
    ]


def test_week_skips_holiday():
    assert working_days(
        date(2026, 10, 19),
        date(2026, 10, 23),
        {date(2026, 10, 21)},
        WEEKEND,
    ) == [
        date(2026, 10, 19),
        date(2026, 10, 20),
        date(2026, 10, 22),
        date(2026, 10, 23),
    ]


def test_range_starting_on_saturday_skips_weekend():
    assert working_days(date(2026, 10, 24), date(2026, 10, 27), set(), WEEKEND) == [
        date(2026, 10, 26),
        date(2026, 10, 27),
    ]


def test_single_weekend_day_returns_empty():
    assert working_days(date(2026, 10, 24), date(2026, 10, 24), set(), WEEKEND) == []


def test_days_in_month_working_counts_month_dates():
    assert days_in_month_working(date(2026, 10, 15), set(), WEEKEND) == 22
