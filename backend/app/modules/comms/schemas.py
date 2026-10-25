from datetime import datetime
from uuid import UUID

from typing import Any

from pydantic import BaseModel, Field, field_validator


class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=10000)

    @field_validator("title", "body", mode="before")
    @classmethod
    def trim_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class Announcement(BaseModel):
    id: UUID
    title: str
    body: str
    posted_by: UUID | None = None
    posted_by_email: str | None = None
    created_at: datetime


class Notification(BaseModel):
    id: UUID
    title: str
    body: str | None = None
    read: bool
    created_at: datetime


class AuditRecord(BaseModel):
    id: int
    actor_id: UUID | None = None
    actor_email: str | None = None
    action: str
    entity: str
    entity_id: str | None = None
    before: Any = None
    after: Any = None
    created_at: datetime
