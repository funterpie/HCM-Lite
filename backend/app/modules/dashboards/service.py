from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from typing import Optional, Dict, Any

async def get_headcount_service(session: AsyncSession, user: Any, department_id: Optional[str] = None) -> int:
    """Get active headcount."""
    try:
        from app.modules.dashboards.repo import get_headcount_repo
        return await get_headcount_repo(session, department_id)
    except Exception:
        return 0

async def get_hr_dashboard_service(session: AsyncSession, user: Any, from_date: Optional[str], to_date: Optional[str], department_id: Optional[str]) -> Dict[str, Any]:
    """HR dashboard metrics wrapper over Taha's repo functions."""
    if user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Admin or HR role required.")
    try:
        from app.modules.dashboards.repo import get_hr_dashboard_repo
        return await get_hr_dashboard_repo(session, from_date, to_date, department_id)
    except Exception as e:
        # Fallback empty structure if repo is pending
        return {
            "kpis": {"headcount": 0, "present": 0, "on_leave": 0, "late_today": 0, "pending_approvals": 0},
            "attendance_trend": [],
            "absenteeism_by_dept": [],
            "leave_by_type": [],
            "top_late": []
        }

async def get_admin_dashboard_service(session: AsyncSession, user: Any, from_date: Optional[str], to_date: Optional[str], department_id: Optional[str]) -> Dict[str, Any]:
    """Admin dashboard metrics wrapper over Taha's repo functions."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required.")
    try:
        from app.modules.dashboards.repo import get_admin_dashboard_repo
        return await get_admin_dashboard_repo(session, from_date, to_date, department_id)
    except Exception as e:
        return {
            "kpis": {"headcount": 0, "attrition_ytd": 0.0, "payroll_cost": 0.0, "avg_salary": 0.0},
            "headcount_by_dept": [],
            "payroll_cost_by_dept": [],
            "gender_split": [],
            "tenure_buckets": [],
            "audit_feed": []
        }

async def get_me_dashboard_service(session: AsyncSession, user: Any) -> Dict[str, Any]:
    """Personal employee dashboard wrapper."""
    if not user.employee_id:
        return {
            "hours_this_week": 0.0,
            "target_hours": 40.0,
            "late_count": 0,
            "leave_balance": [],
            "last_payslip": None,
            "announcements": []
        }
    try:
        from app.modules.dashboards.repo import get_me_dashboard_repo
        return await get_me_dashboard_repo(session, user.employee_id)
    except Exception as e:
        return {
            "hours_this_week": 0.0,
            "target_hours": 40.0,
            "late_count": 0,
            "leave_balance": [],
            "last_payslip": None,
            "announcements": []
        }

async def get_attendance_summary_service(session: AsyncSession, user: Any, from_date: str, to_date: str, department_id: Optional[str]) -> Dict[str, Any]:
    try:
        from app.modules.dashboards.repo import get_attendance_summary_repo
        return await get_attendance_summary_repo(session, from_date, to_date, department_id)
    except Exception:
        return {}

async def get_late_comers_service(session: AsyncSession, user: Any, from_date: str, to_date: str, department_id: Optional[str], limit: int) -> list:
    try:
        from app.modules.dashboards.repo import get_late_comers_repo
        return await get_late_comers_repo(session, from_date, to_date, department_id, limit)
    except Exception:
        return []

async def get_leave_summary_service(session: AsyncSession, user: Any, from_date: str, to_date: str, department_id: Optional[str]) -> list:
    try:
        from app.modules.dashboards.repo import get_leave_summary_repo
        return await get_leave_summary_repo(session, from_date, to_date, department_id)
    except Exception:
        return []

async def get_payroll_summary_service(session: AsyncSession, user: Any, month: str, department_id: Optional[str]) -> Dict[str, Any]:
    try:
        from app.modules.dashboards.repo import get_payroll_summary_repo
        return await get_payroll_summary_repo(session, month, department_id)
    except Exception:
        return {}
