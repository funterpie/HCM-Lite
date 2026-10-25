from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator


class SetupRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    admin_email: EmailStr
    admin_password: SecretStr = Field(min_length=8, max_length=128)

    @field_validator("company_name", mode="before")
    @classmethod
    def trim_company_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class SetupStatusData(BaseModel):
    needs_setup: bool


class SetupStatusResponse(BaseModel):
    data: SetupStatusData


class SetupData(BaseModel):
    admin_id: str
    admin_email: EmailStr
    company_name: str


class SetupResponse(BaseModel):
    data: SetupData


class MeData(BaseModel):
    id: str
    email: EmailStr | None
    role: str
    employee_id: str | None
    must_change_password: bool


class MeResponse(BaseModel):
    data: MeData


class ChangePasswordRequest(BaseModel):
    new_password: SecretStr = Field(min_length=8, max_length=128)


class ChangePasswordData(BaseModel):
    updated: bool


class ChangePasswordResponse(BaseModel):
    data: ChangePasswordData
