from datetime import date
from decimal import Decimal

import pytest

from app.rules.payroll import compute_payslip, compute_tax_monthly, late_penalty_absent_days


@pytest.mark.parametrize(
    ("annual_gross", "expected_monthly_tax"),
    [
        ("600000", "0.00"),
        ("1200000", "2500.00"),
        ("2400000", "17500.00"),
        ("3600000", "42500.00"),
    ],
)
def test_tax_at_each_annual_slab_boundary(annual_gross, expected_monthly_tax):
    monthly_gross = Decimal(annual_gross) / Decimal("12")
    assert compute_tax_monthly(monthly_gross) == Decimal(expected_monthly_tax)


@pytest.mark.parametrize(
    ("annual_gross", "expected_monthly_tax"),
    [
        ("600012", "0.05"),
        ("1200012", "2500.15"),
        ("2400012", "17500.25"),
        ("3600012", "42500.35"),
    ],
)
def test_tax_enters_next_slab_above_each_boundary(annual_gross, expected_monthly_tax):
    monthly_gross = Decimal(annual_gross) / Decimal("12")
    assert compute_tax_monthly(monthly_gross) == Decimal(expected_monthly_tax)


def test_three_lates_add_half_an_absent_day_when_enabled():
    assert late_penalty_absent_days(Decimal("1"), 3, True) == Decimal("1.5")


def test_full_month_without_absences():
    payslip = compute_payslip(
        basic=Decimal("100000"),
        join_date=date(2026, 1, 1),
        exit_date=None,
        month=date(2026, 1, 1),
        working_days_in_month=22,
        payable_working_days=22,
        absent_days=0,
        unpaid_days=0,
        half_days=0,
    )

    assert payslip == {
        "basic": Decimal("100000"),
        "gross": Decimal("150000"),
        "working_days": 22,
        "absent_days": Decimal("0"),
        "unpaid_days": Decimal("0"),
        "half_days": 0,
        "deduction": Decimal("0"),
        "tax": Decimal("10000.00"),
        "net": Decimal("140000.00"),
    }


def test_absences_and_half_day_are_deducted():
    payslip = compute_payslip(
        basic=Decimal("100000"),
        join_date=date(2026, 1, 1),
        exit_date=None,
        month=date(2026, 1, 1),
        working_days_in_month=22,
        payable_working_days=22,
        absent_days=2,
        unpaid_days=0,
        half_days=1,
    )

    assert payslip["deduction"] == Decimal("150000") / Decimal("22") * Decimal("2.5")
    assert payslip["net"] == Decimal("150000") - payslip["deduction"] - Decimal("10000.00")


def test_mid_month_joiner_prorates_gross_but_taxes_full_month_gross():
    payslip = compute_payslip(
        basic=Decimal("100000"),
        join_date=date(2026, 1, 15),
        exit_date=None,
        month=date(2026, 1, 1),
        working_days_in_month=22,
        payable_working_days=11,
        absent_days=0,
        unpaid_days=0,
        half_days=0,
    )

    assert payslip["gross"] == Decimal("75000")
    assert payslip["working_days"] == 11
    assert payslip["tax"] == Decimal("10000.00")
    assert payslip["net"] == Decimal("65000.00")
