"""HTTP routes for employee attendance actions."""

from typing import Any
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_user, require_role
from app.db import get_session
from app.modules.attendance.service import check_in as check_in_service
from app.modules.attendance.service import check_out as check_out_service
from app.modules.attendance.service import get_attendance_board as board_service
from app.modules.attendance.service import get_attendance_calendar as calendar_service
from app.modules.attendance.schemas import (
    AttendanceCorrectionCreate,
    AttendanceCorrectionDecision,
)
from app.modules.attendance.service import (
    decide_attendance_correction,
    list_attendance_corrections,
    request_attendance_correction,
)


router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("/check-in", status_code=201)
async def check_in(
    user: Any = Depends(current_user),
    _: Any = Depends(require_role("employee", "hr")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await check_in_service(session, user)


@router.post("/check-out")
async def check_out(
    user: Any = Depends(current_user),
    _: Any = Depends(require_role("employee", "hr")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await check_out_service(session, user)


@router.get("")
async def get_calendar(
    from_date: date = Query(alias="from"),
    to_date: date = Query(alias="to"),
    employee_id: str | None = None,
    user: Any = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await calendar_service(session, user, from_date, to_date, employee_id)


@router.get("/board")
async def get_board(
    day: date = Query(alias="date"),
    department_id: str | None = None,
    _: Any = Depends(require_role("admin", "hr")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await board_service(session, day, department_id)


@router.post("/corrections", status_code=201)
async def create_correction(
    payload: AttendanceCorrectionCreate,
    user: Any = Depends(current_user),
    _: Any = Depends(require_role("employee")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await request_attendance_correction(
        session,
        user,
        payload.date,
        payload.new_check_in,
        payload.new_check_out,
        payload.reason,
    )


@router.get("/corrections")
async def get_corrections(
    status: str | None = None,
    user: Any = Depends(current_user),
    _: Any = Depends(require_role("employee", "hr", "admin")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await list_attendance_corrections(session, user, status)


@router.patch("/corrections/{correction_id}")
async def decide_correction(
    correction_id: str,
    payload: AttendanceCorrectionDecision,
    user: Any = Depends(current_user),
    _: Any = Depends(require_role("hr")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await decide_attendance_correction(
        session, user, correction_id, payload.decision, payload.comment
    )
