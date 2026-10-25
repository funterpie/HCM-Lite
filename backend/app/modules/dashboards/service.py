from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.modules.comms import repo as comms_repo
from app.modules.dashboards import repo
from app.modules.leave.service import get_leave_balance


async def _local_today(session: AsyncSession) -> date:
    result = await session.execute(
        text(
            "SELECT (clock_timestamp() AT TIME ZONE timezone)::date "
            "FROM settings WHERE id = 1"
        )
    )
    today = result.scalar_one_or_none()
    if today is None:
        raise AppError(400, "settings_not_configured", "Company settings have not been configured.")
    return today


async def _date_range(
    session: AsyncSession, from_date: date | None, to_date: date | None
) -> tuple[date, date]:
    today = await _local_today(session)
    start = from_date or today.replace(month=1, day=1)
    end = to_date or today
    if end < start:
        raise AppError(400, "invalid_date_range", "The end date must be on or after the start date.")
    return start, end


async def get_hr_dashboard(
    session: AsyncSession,
    from_date: date | None,
    to_date: date | None,
    department_id: str | None,
) -> dict[str, Any]:
    start, end = await _date_range(session, from_date, to_date)
    headcount = await repo.get_headcount(session, start, end, department_id)
    present = await repo.get_present_today(session, department_id)
    pending = await repo.get_pending_approvals(session, start, end, department_id)
    return {
        "data": {
            "kpis": {**headcount, **present, **pending},
            "attendance_trend": await repo.get_attendance_trend(session, start, end, department_id),
            "absenteeism_by_dept": await repo.get_absenteeism_by_dept(session, start, end, department_id),
            "leave_by_type": await repo.get_leave_by_type(session, start, end, department_id),
            "top_late": await repo.get_late_comers(
                session, limit=5, from_=start, to=end, department_id=department_id
            ),
        }
    }


async def get_admin_dashboard(
    session: AsyncSession,
    from_date: date | None,
    to_date: date | None,
    department_id: str | None,
) -> dict[str, Any]:
    start, end = await _date_range(session, from_date, to_date)
    headcount = await repo.get_headcount(session, start, end, department_id)
    attrition = await repo.get_attrition(session, start, end)
    payroll = await repo.get_payroll_cost(session, end.replace(day=1), department_id)
    average_salary = await repo.get_average_salary(session, department_id)
    return {
        "data": {
            "kpis": {
                "headcount": headcount["headcount"],
                "monthly_payroll": payroll["gross"],
                "avg_salary": average_salary["average_gross_salary"],
                "attrition_rate": attrition["pct"] or 0,
                "attrition_ytd": attrition["pct"] or 0,
                "payroll_cost": payroll["gross"],
            },
            "attendance_trend": await repo.get_attendance_trend(session, start, end, department_id),
            "absenteeism_by_dept": await repo.get_absenteeism_by_dept(session, start, end, department_id),
            "top_late": await repo.get_late_comers(
                session, limit=5, from_=start, to=end, department_id=department_id
            ),
            "avg_salary_by_dept_designation": await repo.get_avg_salary_by_dept_designation(session),
            "headcount_by_dept": await repo.get_headcount_by_dept(session),
            "payroll_cost_by_dept": await repo.get_payroll_cost_by_dept(session, end.replace(day=1)),
            "gender_split": await repo.get_gender_split(session),
            "tenure_buckets": await repo.get_tenure_buckets(session),
            "audit_feed": await repo.get_audit_feed(session, limit=10),
        }
    }


async def get_me_dashboard(session: AsyncSession, user: Any) -> dict[str, Any]:
    if user.employee_id is None:
        raise AppError(403, "employee_profile_missing", "No employee record is linked to this account.")
    employee_id = str(user.employee_id)
    today = await _local_today(session)
    month_start = today.replace(day=1)
    attendance = await repo.get_today_attendance(session, employee_id)
    leave_balance = await get_leave_balance(session, user)
    announcements = await comms_repo.list_announcements(session)
    return {
        "data": {
            "hours_worked_this_week": (await repo.get_hours_this_week(session, employee_id))["hours"],
            "late_count_month": (await repo.get_late_count(session, employee_id, month_start, today))["late_count"],
            "today_status": attendance["status"] if attendance else "Not checked in",
            "check_in_time": attendance["check_in"].isoformat() if attendance and attendance["check_in"] else None,
            "leave_balance": leave_balance["data"],
            "last_payslip": await repo.get_last_payslip(session, employee_id),
            "announcements": announcements,
        }
    }
