"""Request schemas for attendance corrections."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class AttendanceCorrectionCreate(BaseModel):
    date: date
    new_check_in: datetime | None = None
    new_check_out: datetime | None = None
    reason: str = Field(min_length=1)


class AttendanceCorrectionDecision(BaseModel):
    decision: Literal["approved", "rejected"]
    comment: str | None = None
