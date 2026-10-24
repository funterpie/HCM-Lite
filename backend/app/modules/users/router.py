from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.db import get_db
from app.core.deps import current_user
from app.modules.users.schemas import CreateHRUserRequest, ActiveToggleRequest, ResetPasswordRequest
from app.modules.users.service import create_hr_user_service, set_user_active_service, reset_user_password_service

router = APIRouter(prefix="/users", tags=["Users & HR Logins"])

@router.post("/hr", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_hr_user(payload: CreateHRUserRequest, session: AsyncSession = Depends(get_db), user: Any = Depends(current_user)):
    """Create an HR user login and employee profile (Admin only)."""
    res = await create_hr_user_service(session, user, payload)
    return {"data": res}

@router.patch("/{id}/active", response_model=dict)
async def patch_user_active(id: str, payload: ActiveToggleRequest, session: AsyncSession = Depends(get_db), user: Any = Depends(current_user)):
    """Activate or deactivate user login (Admin only)."""
    res = await set_user_active_service(session, user, id, payload.is_active)
    return {"data": res}

@router.post("/{id}/reset-password", response_model=dict)
async def post_reset_password(id: str, payload: ResetPasswordRequest, session: AsyncSession = Depends(get_db), user: Any = Depends(current_user)):
    """Reset user password (Admin only)."""
    res = await reset_user_password_service(session, user, id, payload.new_password)
    return {"data": res}
