"""HTTP routes for leave requests and balances."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_user, require_role
from app.db import get_session
from app.modules.leave.schemas import LeaveCreate, LeaveDecision
from app.modules.leave.service import (
    apply_leave,
    cancel_leave,
    decide_leave,
    get_leave_balance,
    list_leave,
)


router = APIRouter(prefix="/leave", tags=["leave"])


@router.post("", status_code=201)
async def create_leave(
    payload: LeaveCreate,
    user: Any = Depends(current_user),
    _: Any = Depends(require_role("employee", "hr")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await apply_leave(
        session,
        user,
        payload.leave_type_id,
        payload.start_date,
        payload.end_date,
        payload.reason,
    )


@router.patch("/{leave_id}/cancel")
async def cancel_leave_request(
    leave_id: str,
    user: Any = Depends(current_user),
    _: Any = Depends(require_role("employee", "hr")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await cancel_leave(session, user, leave_id)


@router.get("")
async def get_leave_requests(
    status: str | None = None,
    employee_id: str | None = None,
    user: Any = Depends(current_user),
    _: Any = Depends(require_role("employee", "hr", "admin")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await list_leave(session, user, status, employee_id)


@router.get("/balance")
async def get_balance(
    user: Any = Depends(current_user),
    _: Any = Depends(require_role("employee", "hr")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await get_leave_balance(session, user)


@router.patch("/{leave_id}/decide")
async def decide_leave_request(
    leave_id: str,
    payload: LeaveDecision,
    user: Any = Depends(current_user),
    _: Any = Depends(require_role("hr")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await decide_leave(
        session, user, leave_id, payload.decision, payload.comment
    )
