from datetime import date

import pytest

from app.rules.leave import leave_balance, overlaps


@pytest.mark.parametrize(
    ("quota", "approved_days", "expected"),
    [(14, 5, 9), (8, 8, 0), (10, 12, -2), (None, 100, None)],
)
def test_leave_balance(quota, approved_days, expected):
    assert leave_balance(quota, approved_days) == expected


def test_overlaps_when_ranges_intersect():
    assert overlaps(date(2026, 1, 1), date(2026, 1, 5), date(2026, 1, 5), date(2026, 1, 8))


def test_overlaps_when_one_range_contains_another():
    assert overlaps(date(2026, 1, 1), date(2026, 1, 10), date(2026, 1, 3), date(2026, 1, 5))


def test_overlaps_when_ranges_are_disjoint():
    assert not overlaps(date(2026, 1, 1), date(2026, 1, 4), date(2026, 1, 5), date(2026, 1, 8))
