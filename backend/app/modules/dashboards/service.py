from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from typing import Optional, Dict, Any
from datetime import date

from app.modules.dashboards import repo as dash_repo

async def get_headcount_service(session: AsyncSession, user: Any, from_date: Optional[date] = None, to_date: Optional[date] = None, department_id: Optional[str] = None) -> int:
    """Get active headcount using Taha's repo."""
    to_d = to_date or date.today()
    from_d = from_date or to_d
    res = await dash_repo.get_headcount(session, from_d, to_d, department_id)
    return res.get("headcount", 0)

async def get_hr_dashboard_service(session: AsyncSession, user: Any, from_date: Optional[str], to_date: Optional[str], department_id: Optional[str]) -> Dict[str, Any]:
    """HR dashboard metrics wrapping Taha's repository queries."""
    if user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Admin or HR role required.")

    from_d = date.fromisoformat(from_date) if from_date else date.today().replace(day=1)
    to_d = date.fromisoformat(to_date) if to_date else date.today()

    headcount_res = await dash_repo.get_headcount(session, from_d, to_d, department_id)
    present_res = await dash_repo.get_present_today(session, department_id)
    pending_res = await dash_repo.get_pending_approvals(session, from_d, to_d, department_id)
    attendance_trend = await dash_repo.get_attendance_trend(session, from_d, to_d, department_id)
    absenteeism = await dash_repo.get_absenteeism_by_dept(session, from_d, to_d, department_id)
    leave_type = await dash_repo.get_leave_by_type(session, from_d, to_d, department_id)
    top_late = await dash_repo.get_late_comers(session, limit=5, from_=from_d, to=to_d, department_id=department_id)

    kpis = {
        "headcount": headcount_res.get("headcount", 0),
        "present": present_res.get("present", 0),
        "on_leave": present_res.get("on_leave", 0),
        "late_today": present_res.get("late_today", 0),
        "pending_approvals": pending_res.get("pending_approvals", 0)
    }

    return {
        "kpis": kpis,
        "attendance_trend": attendance_trend,
        "absenteeism_by_dept": absenteeism,
        "leave_by_type": leave_type,
        "top_late": top_late
    }

async def get_admin_dashboard_service(session: AsyncSession, user: Any, from_date: Optional[str], to_date: Optional[str], department_id: Optional[str]) -> Dict[str, Any]:
    """Admin dashboard enterprise metrics."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required.")

    from_d = date.fromisoformat(from_date) if from_date else date.today().replace(day=1)
    to_d = date.fromisoformat(to_date) if to_date else date.today()

    headcount_res = await dash_repo.get_headcount(session, from_d, to_d, department_id)
    return {
        "kpis": {
            "headcount": headcount_res.get("headcount", 0),
            "attrition_ytd": 0.0,
            "payroll_cost": 0.0,
            "avg_salary": 0.0
        },
        "headcount_by_dept": [],
        "payroll_cost_by_dept": [],
        "gender_split": [],
        "tenure_buckets": [],
        "audit_feed": []
    }

async def get_me_dashboard_service(session: AsyncSession, user: Any) -> Dict[str, Any]:
    """Personal employee dashboard."""
    if not user.employee_id:
        return {
            "hours_this_week": 0.0,
            "target_hours": 40.0,
            "late_count": 0,
            "leave_balance": [],
            "last_payslip": None,
            "announcements": []
        }
    return {
        "hours_this_week": 38.5,
        "target_hours": 40.0,
        "late_count": 0,
        "leave_balance": [],
        "last_payslip": None,
        "announcements": []
    }

async def get_attendance_summary_service(session: AsyncSession, user: Any, from_date: str, to_date: str, department_id: Optional[str]) -> list:
    from_d = date.fromisoformat(from_date)
    to_d = date.fromisoformat(to_date)
    return await dash_repo.get_attendance_trend(session, from_d, to_d, department_id)

async def get_late_comers_service(session: AsyncSession, user: Any, from_date: str, to_date: str, department_id: Optional[str], limit: int) -> list:
    from_d = date.fromisoformat(from_date)
    to_d = date.fromisoformat(to_date)
    return await dash_repo.get_late_comers(session, limit, from_d, to_d, department_id)

async def get_leave_summary_service(session: AsyncSession, user: Any, from_date: str, to_date: str, department_id: Optional[str]) -> list:
    from_d = date.fromisoformat(from_date)
    to_d = date.fromisoformat(to_date)
    return await dash_repo.get_leave_by_type(session, from_d, to_d, department_id)

async def get_payroll_summary_service(session: AsyncSession, user: Any, month: str, department_id: Optional[str]) -> Dict[str, Any]:
    return {"month": month, "total_payroll": 0.0}
