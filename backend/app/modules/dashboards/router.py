from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Any

from app.db import get_session
from app.core.deps import current_user
from app.modules.dashboards.service import get_hr_dashboard_service, get_admin_dashboard_service, get_me_dashboard_service

router = APIRouter(prefix="/dashboards", tags=["dashboards"])

@router.get("/hr", response_model=dict)
async def get_hr_dashboard(
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    department_id: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    user: Any = Depends(current_user)
):
    """Get HR dashboard KPI metrics and trends (Admin, HR)."""
    data = await get_hr_dashboard_service(session, user, from_date, to_date, department_id)
    return {"data": data}

@router.get("/admin", response_model=dict)
async def get_admin_dashboard(
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    department_id: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    user: Any = Depends(current_user)
):
    """Get Admin dashboard enterprise metrics (Admin only)."""
    data = await get_admin_dashboard_service(session, user, from_date, to_date, department_id)
    return {"data": data}

@router.get("/me", response_model=dict)
async def get_me_dashboard(
    session: AsyncSession = Depends(get_session),
    user: Any = Depends(current_user)
):
    """Get personal employee dashboard (any role, own scoped data)."""
    data = await get_me_dashboard_service(session, user)
    return {"data": data}
