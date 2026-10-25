from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PayrollRunCreate(BaseModel):
    month: date

    @field_validator("month")
    @classmethod
    def month_must_be_first_day(cls, value: date) -> date:
        if value.day != 1:
            raise ValueError("month must be the first day of the month")
        return value


class Payslip(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: UUID
    employee_id: UUID
    basic: Decimal | None = None
    gross: Decimal | None = None
    working_days: int | None = None
    absent_days: Decimal | None = None
    unpaid_days: Decimal | None = None
    half_days: int | None = None
    deduction: Decimal | None = None
    tax: Decimal | None = None
    net: Decimal | None = None


class PayrollRun(BaseModel):
    id: UUID
    month: date
    status: str
    created_by: UUID | None = None
    finalized_by: UUID | None = None
    finalized_at: datetime | None = None
    payslips: list[Payslip] = Field(default_factory=list)


class PayslipDetail(Payslip):
    month: date
    employee: dict
    company_name: str


class PayrollRunResponse(BaseModel):
    data: PayrollRun


class PayrollRunListResponse(BaseModel):
    data: list[PayrollRun]


class PayslipListResponse(BaseModel):
    data: list[Payslip]
