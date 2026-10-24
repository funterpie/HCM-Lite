from pydantic import BaseModel, EmailStr, Field

class CreateHRUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str
    department_id: str
    designation_id: str
    basic_salary: float = Field(..., gt=0)

class ActiveToggleRequest(BaseModel):
    is_active: bool

class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=6)
