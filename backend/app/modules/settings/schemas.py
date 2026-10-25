from datetime import date, time
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SettingsData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    company_name: str
    timezone: str
    office_start: time
    grace_minutes: int
    half_day_hours: float
    weekend_days: list[int]
    office_lat: float | None
    office_lng: float | None
    office_radius_m: float
    late_penalty_enabled: bool


class SettingsUpdate(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    timezone: str = Field(min_length=1, max_length=100)
    office_start: time
    grace_minutes: int = Field(ge=0)
    half_day_hours: float = Field(gt=0)
    weekend_days: list[int]
    office_lat: float | None = Field(default=None, ge=-90, le=90)
    office_lng: float | None = Field(default=None, ge=-180, le=180)
    office_radius_m: float = Field(gt=0)
    late_penalty_enabled: bool

    @field_validator("company_name", mode="before")
    @classmethod
    def trim_company_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Unknown timezone") from exc
        return value

    @field_validator("weekend_days")
    @classmethod
    def validate_weekend_days(cls, value: list[int]) -> list[int]:
        if any(day < 1 or day > 7 for day in value) or len(set(value)) != len(value):
            raise ValueError("Weekend days must be unique values from 1 to 7")
        return value

    @model_validator(mode="after")
    def validate_office_coordinates(self) -> "SettingsUpdate":
        if (self.office_lat is None) != (self.office_lng is None):
            raise ValueError("Office latitude and longitude must be set together")
        return self


class NamedEntityCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class NamedEntityData(BaseModel):
    id: UUID
    name: str


class LeaveTypeCreate(NamedEntityCreate):
    yearly_quota: int | None = Field(default=None, ge=0)
    is_paid: bool = True


class LeaveTypeData(BaseModel):
    id: UUID
    name: str
    yearly_quota: int | None
    is_paid: bool


class HolidayCreate(BaseModel):
    date: date
    name: str = Field(min_length=1, max_length=200)

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class HolidayData(BaseModel):
    id: UUID
    date: date
    name: str


class EntityPage(BaseModel):
    data: list[Any]
    meta: dict[str, int]


class EntityResponse(BaseModel):
    data: Any


class DeleteData(BaseModel):
    id: UUID
    deleted: bool


class DefaultsData(BaseModel):
    added: list[LeaveTypeData]
