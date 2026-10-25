from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_role
from app.core.errors import AppError
from app.db import get_session
from app.modules.users import service
from app.modules.users.schemas import ActiveUpdate, HrUserCreate, ManagedUser, PasswordReset

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[ManagedUser])
async def list_users(
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[CurrentUser, Depends(require_role("admin"))],
) -> list[ManagedUser]:
    return [ManagedUser(**row) for row in await service.list_users(session)]


@router.post("/hr", response_model=ManagedUser, status_code=status.HTTP_201_CREATED)
async def create_hr_user(
    payload: HrUserCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(require_role("admin"))],
) -> ManagedUser:
    result = await service.create_hr_user(
        session, user.id, str(payload.email), payload.temp_password.get_secret_value()
    )
    return ManagedUser(**result)


@router.patch("/{user_id}/active")
async def update_user_active(
    user_id: UUID,
    payload: ActiveUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(require_role("admin"))],
) -> dict:
    if user.id == user_id and not payload.is_active:
        raise AppError(409, "cannot_disable_self", "You cannot disable your own account.")
    return await service.set_active(session, user.id, user_id, payload.is_active)


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: UUID,
    payload: PasswordReset,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(require_role("admin"))],
) -> dict:
    return await service.reset_password(
        session, user.id, user_id, payload.temp_password.get_secret_value()
    )
