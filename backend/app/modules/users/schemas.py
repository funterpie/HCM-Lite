from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, SecretStr


class HrUserCreate(BaseModel):
    email: EmailStr
    temp_password: SecretStr = Field(min_length=8, max_length=128)


class PasswordReset(BaseModel):
    temp_password: SecretStr = Field(min_length=8, max_length=128)


class ActiveUpdate(BaseModel):
    is_active: bool


class ManagedUser(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    is_active: bool
    must_change_password: bool
