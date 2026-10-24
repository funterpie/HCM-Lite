from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, current_user
from app.db import get_session
from app.modules.auth import service
from app.modules.auth.schemas import (
    ChangePasswordData,
    ChangePasswordRequest,
    ChangePasswordResponse,
    MeData,
    MeResponse,
    SetupData,
    SetupRequest,
    SetupResponse,
    SetupStatusData,
    SetupStatusResponse,
)

router = APIRouter(tags=["auth"])


@router.get("/setup/status", response_model=SetupStatusResponse)
async def get_setup_status(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SetupStatusResponse:
    return SetupStatusResponse(data=SetupStatusData(**await service.get_setup_status(session)))


@router.post("/setup", response_model=SetupResponse, status_code=status.HTTP_201_CREATED)
async def setup(
    payload: SetupRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SetupResponse:
    result = await service.setup_company(
        session,
        payload.company_name.strip(),
        str(payload.admin_email),
        payload.admin_password.get_secret_value(),
    )
    return SetupResponse(data=SetupData(**result))


@router.get("/me", response_model=MeResponse)
async def get_me(
    user: Annotated[CurrentUser, Depends(current_user)],
) -> MeResponse:
    return MeResponse(data=MeData(**await service.get_me(user)))


@router.post("/auth/change-password", response_model=ChangePasswordResponse)
async def post_change_password(
    payload: ChangePasswordRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(current_user)],
) -> ChangePasswordResponse:
    await service.change_password(
        session, user, payload.new_password.get_secret_value()
    )
    return ChangePasswordResponse(data=ChangePasswordData(updated=True))
