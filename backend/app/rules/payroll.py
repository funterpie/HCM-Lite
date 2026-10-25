"""Pure payroll and illustrative income-tax calculations."""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP


ZERO = Decimal("0")
TWELVE = Decimal("12")
CENT = Decimal("0.01")


def _decimal(value: Decimal | int | str) -> Decimal:
    """Convert numeric inputs without introducing binary floating-point error."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def compute_tax_monthly(gross_monthly: Decimal) -> Decimal:
    """Compute monthly tax from annualized gross using the project tax slabs."""
    annual_gross = _decimal(gross_monthly) * TWELVE
    if annual_gross <= Decimal("600000"):
        annual_tax = ZERO
    elif annual_gross <= Decimal("1200000"):
        annual_tax = (annual_gross - Decimal("600000")) * Decimal("0.05")
    elif annual_gross <= Decimal("2400000"):
        annual_tax = Decimal("30000") + (annual_gross - Decimal("1200000")) * Decimal("0.15")
    elif annual_gross <= Decimal("3600000"):
        annual_tax = Decimal("210000") + (annual_gross - Decimal("2400000")) * Decimal("0.25")
    else:
        annual_tax = Decimal("510000") + (annual_gross - Decimal("3600000")) * Decimal("0.35")

    return (annual_tax / TWELVE).quantize(CENT, rounding=ROUND_HALF_UP)


def compute_payslip(
    basic: Decimal,
    join_date: date,
    exit_date: date | None,
    month: date,
    working_days_in_month: int,
    payable_working_days: int,
    absent_days: Decimal | int,
    unpaid_days: Decimal | int,
    half_days: int,
) -> dict[str, Decimal | int]:
    """Calculate gross, deductions, monthly tax, and net pay for one employee."""
    del join_date, exit_date, month  # Proration is supplied as payable_working_days.

    basic_amount = _decimal(basic)
    absent = _decimal(absent_days)
    unpaid = _decimal(unpaid_days)
    half = _decimal(half_days)
    gross = basic_amount * Decimal("1.5")

    if working_days_in_month <= 0:
        raise ValueError("working_days_in_month must be greater than zero")
    if payable_working_days < 0 or payable_working_days > working_days_in_month:
        raise ValueError("payable_working_days must be between zero and working_days_in_month")

    per_day = gross / Decimal(working_days_in_month)
    prorated_gross = per_day * Decimal(payable_working_days)
    deduction = per_day * (absent + unpaid + Decimal("0.5") * half)
    tax = compute_tax_monthly(gross)
    net = prorated_gross - deduction - tax

    return {
        "basic": basic_amount,
        "gross": prorated_gross,
        "working_days": payable_working_days,
        "absent_days": absent,
        "unpaid_days": unpaid,
        "half_days": half_days,
        "deduction": deduction,
        "tax": tax,
        "net": net,
    }
