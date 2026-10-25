from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=20)


class SummarizeRequest(BaseModel):
    dashboard: Literal["hr", "admin"]
    from_date: date | None = Field(default=None, alias="from")
    to_date: date | None = Field(default=None, alias="to")
    department_id: UUID | None = None


class SmartLeaveRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
