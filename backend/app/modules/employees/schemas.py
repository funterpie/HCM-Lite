from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator, model_validator


class EmployeeFields(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=40)
    address: str | None = Field(default=None, max_length=500)
    gender: str | None = Field(default=None, max_length=40)
    department_id: UUID | None = None
    designation_id: UUID | None = None
    join_date: date
    status: Literal["active", "probation", "exited"] = "active"

    @field_validator("code", "full_name", mode="before")
    @classmethod
    def trim_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class EmployeeCreate(EmployeeFields):
    basic_salary: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    temp_password: SecretStr = Field(min_length=8, max_length=128)


class EmployeeUpdate(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    full_name: str = Field(min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=40)
    address: str | None = Field(default=None, max_length=500)
    gender: str | None = Field(default=None, max_length=40)
    department_id: UUID | None = None
    designation_id: UUID | None = None
    join_date: date
    status: Literal["active", "probation", "exited"]

    @field_validator("code", "full_name", mode="before")
    @classmethod
    def trim_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class SalaryUpdate(BaseModel):
    basic_salary: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class ProfileUpdate(BaseModel):
    phone: str | None = Field(default=None, max_length=40)
    address: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "ProfileUpdate":
        if not self.model_fields_set:
            raise ValueError("Provide phone or address")
        return self


class EmployeePage(BaseModel):
    data: list[dict]
    meta: dict[str, int]


class EmployeeResponse(BaseModel):
    data: dict

