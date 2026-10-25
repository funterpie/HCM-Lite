"""Request schemas for leave endpoints."""

from datetime import date
from typing import Literal

from pydantic import BaseModel


class LeaveCreate(BaseModel):
    leave_type_id: str
    start_date: date
    end_date: date
    reason: str | None = None


class LeaveDecision(BaseModel):
    decision: Literal["approved", "rejected"]
    comment: str | None = None
