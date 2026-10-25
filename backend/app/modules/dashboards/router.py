from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_role
from app.db import get_session
from app.modules.dashboards import service

router = APIRouter(prefix="/dashboard", tags=["dashboards"])


@router.get("/hr")
async def get_hr_dashboard(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    department_id: str | None = None,
    _: CurrentUser = Depends(require_role("admin", "hr")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await service.get_hr_dashboard(session, from_date, to_date, department_id)


@router.get("/admin")
async def get_admin_dashboard(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    department_id: str | None = None,
    _: CurrentUser = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await service.get_admin_dashboard(session, from_date, to_date, department_id)


@router.get("/me")
async def get_me_dashboard(
    user: CurrentUser = Depends(require_role("employee")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await service.get_me_dashboard(session, user)
