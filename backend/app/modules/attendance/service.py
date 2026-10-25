"""Attendance check-in and check-out service functions."""

from calendar import monthrange
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import scoped_employee_id
from app.core.errors import AppError
from app.core.audit import log as audit_log
from app.core.notify import notify
from app.rules.attendance import Settings, attendance_status, daily_status
from app.rules.calendar import working_days
from app.rules.payroll import late_penalty_absent_days


async def _settings(session: AsyncSession) -> Settings:
    result = await session.execute(
        text(
            "SELECT office_start, grace_minutes, half_day_hours, timezone, weekend_days, "
            "late_penalty_enabled FROM settings WHERE id = 1"
        )
    )
    row = result.mappings().first()
    if row is None:
        raise AppError(400, "settings_not_configured", "Company settings have not been configured.")
    return Settings(
        office_start=row["office_start"],
        grace_minutes=row["grace_minutes"],
        half_day_hours=float(row["half_day_hours"]),
        timezone=row["timezone"],
        weekend_days=set(row["weekend_days"] or {6, 7}),
        late_penalty_enabled=bool(row["late_penalty_enabled"]),
    )


def _employee_id(user: Any) -> Any:
    employee_id = user.get("employee_id") if isinstance(user, dict) else getattr(user, "employee_id", None)
    if employee_id is None:
        raise AppError(403, "employee_record_required", "The signed-in user has no employee record.")
    return employee_id


def _today(settings: Settings) -> date:
    return datetime.now(timezone.utc).astimezone(ZoneInfo(settings.timezone)).date()


def _response(row: Any) -> dict[str, Any]:
    return {
        "data": {
            "date": row["date"].isoformat(),
            "check_in": row["check_in"].isoformat() if row["check_in"] else None,
            "check_out": row["check_out"].isoformat() if row["check_out"] else None,
            "status": row["status"],
        }
    }


async def check_in(session: AsyncSession, user: Any) -> dict[str, Any]:
    """Stamp a check-in using server UTC time for the caller's own employee row."""
    settings = await _settings(session)
    employee_id = _employee_id(user)
    now = datetime.now(timezone.utc)
    work_date = now.astimezone(ZoneInfo(settings.timezone)).date()
    status = attendance_status(now, None, settings)

    try:
        result = await session.execute(
            text(
                "INSERT INTO attendance (employee_id, date, check_in, status, source) "
                "VALUES (:employee_id, :work_date, :check_in, :status, 'web') "
                "ON CONFLICT (employee_id, date) DO NOTHING "
                "RETURNING date, check_in, check_out, status"
            ),
            {
                "employee_id": employee_id,
                "work_date": work_date,
                "check_in": now,
                "status": status,
            },
        )
        row = result.mappings().first()
        if row is None:
            await session.rollback()
            raise AppError(409, "already_checked_in", "You have already checked in today.")
        await session.commit()
        return _response(row)
    except IntegrityError as exc:
        await session.rollback()
        raise AppError(409, "already_checked_in", "You have already checked in today.") from exc


async def check_out(session: AsyncSession, user: Any) -> dict[str, Any]:
    """Stamp check-out with server UTC time and recompute the record status."""
    settings = await _settings(session)
    employee_id = _employee_id(user)
    now = datetime.now(timezone.utc)
    work_date = _today(settings)

    result = await session.execute(
        text(
            "SELECT date, check_in, check_out, status FROM attendance "
            "WHERE employee_id = :employee_id AND date = :work_date FOR UPDATE"
        ),
        {"employee_id": employee_id, "work_date": work_date},
    )
    row = result.mappings().first()
    if row is None or row["check_in"] is None:
        raise AppError(409, "not_checked_in", "You must check in before checking out.")
    if row["check_out"] is not None:
        raise AppError(409, "already_checked_out", "You have already checked out today.")

    status = attendance_status(row["check_in"], now, settings)
    updated = await session.execute(
        text(
            "UPDATE attendance SET check_out = :check_out, status = :status "
            "WHERE employee_id = :employee_id AND date = :work_date "
            "RETURNING date, check_in, check_out, status"
        ),
        {
            "employee_id": employee_id,
            "work_date": work_date,
            "check_out": now,
            "status": status,
        },
    )
    updated_row = updated.mappings().one()
    await session.commit()
    return _response(updated_row)


async def _attendance_days(
    session: AsyncSession,
    start: date,
    end: date,
    employee_id: str | None = None,
    department_id: str | None = None,
    active_only: bool = False,
    active_or_probation: bool = False,
) -> tuple[Settings, list[dict[str, Any]]]:
    settings = await _settings(session)
    employee_query = (
        "SELECT e.id, e.full_name, e.join_date, e.exit_date, e.status, e.department_id "
        "FROM employees e "
        "WHERE e.join_date <= :end_date "
        "AND (e.exit_date IS NULL OR e.exit_date >= :start_date) "
        "AND (:employee_id IS NULL OR e.id = CAST(:employee_id AS uuid)) "
        "AND (:department_id IS NULL OR e.department_id = CAST(:department_id AS uuid)) "
    )
    if active_only:
        employee_query += "AND e.status = 'active' "
    elif active_or_probation:
        employee_query += "AND e.status IN ('active', 'probation') "
    else:
        employee_query += "AND (e.status <> 'exited' OR e.exit_date >= :start_date) "
    employee_result = await session.execute(
        text(employee_query),
        {
            "start_date": start,
            "end_date": end,
            "employee_id": employee_id,
            "department_id": department_id,
        },
    )
    employees = [dict(row) for row in employee_result.mappings().all()]
    if not employees:
        return settings, []

    ids = [row["id"] for row in employees]
    attendance_result = await session.execute(
        text(
            "SELECT employee_id, date, check_in, check_out FROM attendance "
            "WHERE employee_id = ANY(:employee_ids) AND date BETWEEN :start_date AND :end_date"
        ),
        {"employee_ids": ids, "start_date": start, "end_date": end},
    )
    records = {
        (str(row["employee_id"]), row["date"]): dict(row)
        for row in attendance_result.mappings().all()
    }
    leave_result = await session.execute(
        text(
            "SELECT employee_id, start_date, end_date FROM leave_requests "
            "WHERE employee_id = ANY(:employee_ids) AND status = 'approved' "
            "AND start_date <= :end_date AND end_date >= :start_date"
        ),
        {"employee_ids": ids, "start_date": start, "end_date": end},
    )
    approved_ranges: dict[str, list[tuple[date, date]]] = {}
    for leave in leave_result.mappings().all():
        approved_ranges.setdefault(str(leave["employee_id"]), []).append(
            (leave["start_date"], leave["end_date"])
        )
    holiday_result = await session.execute(
        text("SELECT date FROM holidays WHERE date BETWEEN :start_date AND :end_date"),
        {"start_date": start, "end_date": end},
    )
    holidays = {row["date"] for row in holiday_result.mappings().all()}
    today = _today(settings)

    output: list[dict[str, Any]] = []
    for employee in employees:
        employee_key = str(employee["id"])
        for day in _date_range(start, end):
            record = records.get((employee_key, day))
            is_on_leave = any(
                leave_start <= day <= leave_end
                for leave_start, leave_end in approved_ranges.get(employee_key, [])
            )
            status = daily_status(
                day=day,
                employee_join=employee["join_date"],
                employee_exit=employee["exit_date"],
                record=record,
                approved_leave=is_on_leave,
                holidays=holidays,
                s=settings,
                today=today,
            )
            output.append(
                {
                    "employee_id": employee["id"],
                    "employee": employee["full_name"],
                    "department_id": employee["department_id"],
                    "date": day.isoformat(),
                    "status": status,
                    "check_in": record["check_in"].isoformat()
                    if record and record["check_in"]
                    else None,
                    "check_out": record["check_out"].isoformat()
                    if record and record["check_out"]
                    else None,
                }
            )
    return settings, output


def _date_range(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _employee_scope(user: Any, requested_employee_id: str | None) -> str | None:
    own_id = scoped_employee_id(user)
    return str(own_id) if own_id is not None else requested_employee_id


async def get_attendance_calendar(
    session: AsyncSession,
    user: Any,
    start: date,
    end: date,
    employee_id: str | None = None,
) -> dict[str, Any]:
    """Return daily computed attendance, forcing Employee callers to their own row."""
    if end < start:
        raise AppError(400, "invalid_date_range", "The end date must be on or after the start date.")
    employee_filter = _employee_scope(user, employee_id)
    _, days = await _attendance_days(session, start, end, employee_id=employee_filter)
    return {"data": days}


async def get_attendance_board(
    session: AsyncSession,
    day: date,
    department_id: str | None = None,
) -> dict[str, Any]:
    """Return one computed attendance row per active employee and status counts."""
    _, days = await _attendance_days(
        session,
        day,
        day,
        department_id=department_id,
        active_only=True,
    )
    counts = {
        status: sum(1 for row in days if row["status"] == status)
        for status in ("present", "late", "half_day", "missing_checkout", "absent", "on_leave")
    }
    return {"data": {"date": day.isoformat(), "rows": days, "counts": counts}}


async def get_attendance_summary(
    session: AsyncSession,
    user: Any,
    from_date: date,
    to_date: date,
    department_id: str | None = None,
) -> dict[str, Any]:
    """Summarize computed attendance for dashboards and AI tools."""
    if to_date < from_date:
        raise AppError(400, "invalid_date_range", "The end date must be on or after the start date.")
    employee_filter = _employee_scope(user, None)
    _, days = await _attendance_days(
        session,
        from_date,
        to_date,
        employee_id=employee_filter,
        department_id=department_id,
    )
    statuses = ("present", "late", "half_day", "missing_checkout", "absent", "on_leave")
    counts = {status: sum(1 for row in days if row["status"] == status) for status in statuses}
    working_days_excluding_leave = sum(
        1 for row in days if row["status"] is not None and row["status"] != "on_leave"
    )
    attendance_units = (
        counts["present"]
        + counts["late"]
        + counts["missing_checkout"]
        + Decimal("0.5") * counts["half_day"]
    )
    attendance_rate = (
        float(attendance_units / working_days_excluding_leave * 100)
        if working_days_excluding_leave
        else 0.0
    )
    late_by_employee: dict[str, dict[str, Any]] = {}
    for row in days:
        if row["status"] == "late":
            key = str(row["employee_id"])
            late_by_employee.setdefault(
                key,
                {"employee_id": row["employee_id"], "employee": row["employee"], "count": 0},
            )["count"] += 1
    late_counts = sorted(late_by_employee.values(), key=lambda item: (-item["count"], item["employee"]))
    return {
        "counts": counts,
        "attendance_rate": round(attendance_rate, 2),
        "late_counts": late_counts,
    }


async def payroll_inputs(session: AsyncSession, month: date) -> list[dict[str, Any]]:
    """Build payroll day inputs from shared computed attendance statuses."""
    month_start = month.replace(day=1)
    month_end = month.replace(day=monthrange(month.year, month.month)[1])
    settings, status_rows = await _attendance_days(
        session,
        month_start,
        month_end,
        active_or_probation=True,
    )
    if not status_rows:
        return []

    employee_ids = list({str(row["employee_id"]) for row in status_rows})
    employee_result = await session.execute(
        text(
            "SELECT id, basic_salary, join_date, exit_date FROM employees "
            "WHERE id = ANY(:employee_ids)"
        ),
        {"employee_ids": employee_ids},
    )
    employees = {str(row["id"]): dict(row) for row in employee_result.mappings().all()}

    holiday_result = await session.execute(
        text("SELECT date FROM holidays WHERE date BETWEEN :start_date AND :end_date"),
        {"start_date": month_start, "end_date": month_end},
    )
    holidays = {row["date"] for row in holiday_result.mappings().all()}
    weekend = settings.weekend_days
    working_in_month = len(working_days(month_start, month_end, holidays, weekend))

    unpaid_result = await session.execute(
        text(
            "SELECT lr.employee_id, lr.start_date, lr.end_date "
            "FROM leave_requests lr JOIN leave_types lt ON lt.id = lr.leave_type_id "
            "WHERE lr.employee_id = ANY(:employee_ids) AND lr.status = 'approved' "
            "AND lt.is_paid = false AND lr.start_date <= :month_end "
            "AND lr.end_date >= :month_start"
        ),
        {
            "employee_ids": employee_ids,
            "month_start": month_start,
            "month_end": month_end,
        },
    )
    unpaid_ranges: dict[str, list[tuple[date, date]]] = {}
    for row in unpaid_result.mappings().all():
        unpaid_ranges.setdefault(str(row["employee_id"]), []).append(
            (row["start_date"], row["end_date"])
        )

    statuses_by_employee: dict[str, list[dict[str, Any]]] = {}
    for row in status_rows:
        statuses_by_employee.setdefault(str(row["employee_id"]), []).append(row)

    inputs = []
    for employee_id, employee in employees.items():
        join_date = employee["join_date"]
        exit_date = employee["exit_date"]
        payable_start = max(join_date, month_start)
        payable_end = min(exit_date or month_end, month_end)
        payable_days = working_days(payable_start, payable_end, holidays, weekend)
        payable_date_set = set(payable_days)
        relevant_statuses = [
            row for row in statuses_by_employee.get(employee_id, [])
            if date.fromisoformat(row["date"]) in payable_date_set
        ]
        absent_days = sum(row["status"] == "absent" for row in relevant_statuses)
        late_days = sum(row["status"] == "late" for row in relevant_statuses)
        absent_days = late_penalty_absent_days(
            absent_days, late_days, settings.late_penalty_enabled
        )
        half_days = sum(row["status"] == "half_day" for row in relevant_statuses)

        unpaid_dates: set[date] = set()
        for leave_start, leave_end in unpaid_ranges.get(employee_id, []):
            clipped_start = max(leave_start, payable_start)
            clipped_end = min(leave_end, payable_end)
            unpaid_dates.update(working_days(clipped_start, clipped_end, holidays, weekend))

        inputs.append(
            {
                "employee_id": employee_id,
                "basic_salary": employee["basic_salary"],
                "join_date": join_date,
                "exit_date": exit_date,
                "working_days_in_month": working_in_month,
                "payable_working_days": len(payable_days),
                "absent_days": absent_days,
                "unpaid_days": len(unpaid_dates),
                "half_days": half_days,
            }
        )
    return inputs


def _correction_dict(row: Any) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "employee_id": str(row["employee_id"]),
        "date": row["date"].isoformat(),
        "new_check_in": row["new_check_in"].isoformat() if row["new_check_in"] else None,
        "new_check_out": row["new_check_out"].isoformat() if row["new_check_out"] else None,
        "reason": row["reason"],
        "status": row["status"],
        "hr_comment": row["hr_comment"],
        "decided_by": str(row["decided_by"]) if row["decided_by"] else None,
        "decided_at": row["decided_at"].isoformat() if row["decided_at"] else None,
    }


async def request_attendance_correction(
    session: AsyncSession,
    user: Any,
    day: date,
    new_check_in: datetime | None,
    new_check_out: datetime | None,
    reason: str,
) -> dict[str, Any]:
    """Create a pending correction request for the caller's own employee record."""
    employee_id = _employee_id(user)
    if not reason.strip():
        raise AppError(400, "reason_required", "A correction reason is required.")
    if new_check_in is None and new_check_out is None:
        raise AppError(400, "correction_time_required", "Provide a corrected check-in or check-out time.")
    result = await session.execute(
        text(
            "INSERT INTO attendance_corrections "
            "(employee_id, date, new_check_in, new_check_out, reason, status) "
            "VALUES (:employee_id, :day, :new_check_in, :new_check_out, :reason, 'pending') "
            "RETURNING id, employee_id, date, new_check_in, new_check_out, reason, status, "
            "hr_comment, decided_by, decided_at"
        ),
        {
            "employee_id": employee_id,
            "day": day,
            "new_check_in": new_check_in,
            "new_check_out": new_check_out,
            "reason": reason.strip(),
        },
    )
    row = result.mappings().one()
    await session.commit()
    return {"data": _correction_dict(row)}


async def list_attendance_corrections(
    session: AsyncSession,
    user: Any,
    status: str | None = None,
) -> dict[str, Any]:
    """List corrections, forcing Employee callers to their own employee id."""
    employee_id = scoped_employee_id(user)
    if status is not None and status not in {"pending", "approved", "rejected", "cancelled"}:
        raise AppError(400, "invalid_status", "The requested correction status is invalid.")
    result = await session.execute(
        text(
            "SELECT id, employee_id, date, new_check_in, new_check_out, reason, status, "
            "hr_comment, decided_by, decided_at FROM attendance_corrections "
            "WHERE (:employee_id IS NULL OR employee_id = CAST(:employee_id AS uuid)) "
            "AND (:status IS NULL OR status = CAST(:status AS req_status)) "
            "ORDER BY date DESC, id DESC"
        ),
        {"employee_id": str(employee_id) if employee_id is not None else None, "status": status},
    )
    return {"data": [_correction_dict(row) for row in result.mappings().all()]}


def _actor_id(user: Any) -> Any:
    value = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)
    if value is None:
        raise AppError(401, "unauthenticated", "Authentication is required.")
    return value


async def decide_attendance_correction(
    session: AsyncSession,
    user: Any,
    correction_id: str,
    decision: str,
    comment: str | None = None,
) -> dict[str, Any]:
    """Approve or reject a pending correction; only HR routes to this service."""
    if decision not in {"approved", "rejected"}:
        raise AppError(400, "invalid_decision", "Decision must be approved or rejected.")

    result = await session.execute(
        text(
            "SELECT id, employee_id, date, new_check_in, new_check_out, reason, status, "
            "hr_comment, decided_by, decided_at FROM attendance_corrections "
            "WHERE id = CAST(:correction_id AS uuid) FOR UPDATE"
        ),
        {"correction_id": correction_id},
    )
    correction = result.mappings().first()
    if correction is None:
        raise AppError(404, "correction_not_found", "The attendance correction was not found.")
    if correction["status"] != "pending":
        raise AppError(409, "correction_already_decided", "The attendance correction was already decided.")

    actor_id = _actor_id(user)
    now = datetime.now(timezone.utc)
    before = _correction_dict(correction)
    if decision == "approved":
        settings = await _settings(session)
        existing_result = await session.execute(
            text(
                "SELECT check_in, check_out FROM attendance "
                "WHERE employee_id = :employee_id AND date = :day FOR UPDATE"
            ),
            {"employee_id": correction["employee_id"], "day": correction["date"]},
        )
        existing_attendance = existing_result.mappings().first()
        check_in = correction["new_check_in"] or (
            existing_attendance["check_in"] if existing_attendance else None
        )
        check_out = correction["new_check_out"] or (
            existing_attendance["check_out"] if existing_attendance else None
        )
        status = attendance_status(
            check_in, check_out, settings
        )
        await session.execute(
            text(
                "INSERT INTO attendance (employee_id, date, check_in, check_out, status, source) "
                "VALUES (:employee_id, :day, :check_in, :check_out, :status, 'correction') "
                "ON CONFLICT (employee_id, date) DO UPDATE SET "
                "check_in = COALESCE(EXCLUDED.check_in, attendance.check_in), "
                "check_out = COALESCE(EXCLUDED.check_out, attendance.check_out), "
                "status = EXCLUDED.status, source = 'correction'"
            ),
            {
                "employee_id": correction["employee_id"],
                "day": correction["date"],
                "check_in": check_in,
                "check_out": check_out,
                "status": status,
            },
        )

    decided = await session.execute(
        text(
            "UPDATE attendance_corrections SET status = CAST(:decision AS req_status), "
            "hr_comment = :comment, decided_by = CAST(:actor_id AS uuid), decided_at = :now "
            "WHERE id = CAST(:correction_id AS uuid) "
            "RETURNING id, employee_id, date, new_check_in, new_check_out, reason, status, "
            "hr_comment, decided_by, decided_at"
        ),
        {
            "decision": decision,
            "comment": comment,
            "actor_id": actor_id,
            "now": now,
            "correction_id": correction_id,
        },
    )
    updated = decided.mappings().one()
    after = _correction_dict(updated)
    await audit_log(
        session,
        _actor_id(user),
        f"attendance_correction_{decision}",
        "attendance_correction",
        correction_id,
        before,
        after,
    )
    employee_result = await session.execute(
        text("SELECT user_id FROM employees WHERE id = :employee_id"),
        {"employee_id": correction["employee_id"]},
    )
    employee_user_id = employee_result.scalar_one_or_none()
    if employee_user_id is not None:
        await notify(
            session,
            employee_user_id,
            f"Attendance correction {decision}",
            f"Your attendance correction for {correction['date'].isoformat()} was {decision}.",
        )
    await session.commit()
    return {"data": after}
