"""Leave request services backed by pure calendar and balance rules."""

from datetime import date, datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log as audit_log
from app.core.deps import scoped_employee_id
from app.core.errors import AppError
from app.core.notify import notify
from app.rules.calendar import working_days
from app.rules.leave import leave_balance, overlaps


def _value(user: Any, key: str) -> Any:
    return user.get(key) if isinstance(user, dict) else getattr(user, key, None)


def _own_employee_id(user: Any) -> Any:
    value = _value(user, "employee_id")
    if value is None:
        raise AppError(403, "employee_record_required", "The signed-in user has no employee record.")
    return value


def _actor_id(user: Any) -> Any:
    value = _value(user, "id")
    if value is None:
        raise AppError(401, "unauthenticated", "Authentication is required.")
    return value


async def _calendar_settings(session: AsyncSession) -> tuple[set[date], set[int], str]:
    result = await session.execute(
        text("SELECT timezone, weekend_days FROM settings WHERE id = 1")
    )
    row = result.mappings().first()
    if row is None:
        raise AppError(400, "settings_not_configured", "Company settings have not been configured.")
    holidays_result = await session.execute(text("SELECT date FROM holidays"))
    holidays = {item["date"] for item in holidays_result.mappings().all()}
    return holidays, set(row["weekend_days"] or {6, 7}), row["timezone"]


def _today(timezone_name: str) -> date:
    return datetime.now(timezone.utc).astimezone(ZoneInfo(timezone_name)).date()


def _iso(value: Any) -> Any:
    return value.isoformat() if hasattr(value, "isoformat") else value


def _leave_dict(row: Any) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "employee_id": str(row["employee_id"]),
        "leave_type_id": str(row["leave_type_id"]),
        "start_date": row["start_date"].isoformat(),
        "end_date": row["end_date"].isoformat(),
        "days": row["days"],
        "reason": row["reason"],
        "status": row["status"],
        "hr_comment": row["hr_comment"],
        "created_at": _iso(row["created_at"]),
    }


async def _approved_days_in_year(
    session: AsyncSession,
    employee_id: str,
    leave_type_id: str,
    year: int,
    holidays: set[date],
    weekend: set[int],
) -> int:
    year_start, year_end = date(year, 1, 1), date(year, 12, 31)
    result = await session.execute(
        text(
            "SELECT start_date, end_date FROM leave_requests "
            "WHERE employee_id = CAST(:employee_id AS uuid) "
            "AND leave_type_id = CAST(:leave_type_id AS uuid) "
            "AND status = 'approved' AND start_date <= :year_end AND end_date >= :year_start"
        ),
        {
            "employee_id": employee_id,
            "leave_type_id": leave_type_id,
            "year_start": year_start,
            "year_end": year_end,
        },
    )
    total = 0
    for row in result.mappings().all():
        start, end = max(row["start_date"], year_start), min(row["end_date"], year_end)
        total += len(working_days(start, end, holidays, weekend))
    return total


async def apply_leave(
    session: AsyncSession,
    user: Any,
    leave_type_id: str,
    start_date: date,
    end_date: date,
    reason: str | None = None,
) -> dict[str, Any]:
    """Create a pending leave request after working-day, overlap, and quota checks."""
    if end_date < start_date:
        raise AppError(400, "invalid_date_range", "The end date must be on or after the start date.")
    employee_id = _own_employee_id(user)
    holidays, weekend, _ = await _calendar_settings(session)
    requested_days = working_days(start_date, end_date, holidays, weekend)
    if not requested_days:
        raise AppError(422, "no_working_days", "The requested range contains no working days.")

    type_result = await session.execute(
        text("SELECT id, yearly_quota FROM leave_types WHERE id = CAST(:id AS uuid)"),
        {"id": leave_type_id},
    )
    leave_type = type_result.mappings().first()
    if leave_type is None:
        raise AppError(404, "leave_type_not_found", "The selected leave type was not found.")

    existing_result = await session.execute(
        text(
            "SELECT start_date, end_date FROM leave_requests "
            "WHERE employee_id = CAST(:employee_id AS uuid) "
            "AND status IN ('pending', 'approved') "
            "AND start_date <= :end_date AND end_date >= :start_date"
        ),
        {"employee_id": employee_id, "start_date": start_date, "end_date": end_date},
    )
    if any(
        overlaps(start_date, end_date, row["start_date"], row["end_date"])
        for row in existing_result.mappings().all()
    ):
        raise AppError(422, "overlap", "The request overlaps another pending or approved leave request.")

    quota = leave_type["yearly_quota"]
    if quota is not None:
        years = {day.year for day in requested_days}
        for year in years:
            requested_in_year = sum(day.year == year for day in requested_days)
            used = await _approved_days_in_year(
                session, employee_id, leave_type_id, year, holidays, weekend
            )
            remaining = leave_balance(quota, used)
            if remaining is not None and requested_in_year > remaining:
                raise AppError(422, "insufficient_balance", "The request exceeds the remaining leave balance.")

    inserted = await session.execute(
        text(
            "INSERT INTO leave_requests "
            "(employee_id, leave_type_id, start_date, end_date, days, reason, status) "
            "VALUES (CAST(:employee_id AS uuid), CAST(:leave_type_id AS uuid), "
            ":start_date, :end_date, :days, :reason, 'pending') "
            "RETURNING id, employee_id, leave_type_id, start_date, end_date, days, reason, "
            "status, hr_comment, created_at"
        ),
        {
            "employee_id": employee_id,
            "leave_type_id": leave_type_id,
            "start_date": start_date,
            "end_date": end_date,
            "days": len(requested_days),
            "reason": reason,
        },
    )
    row = inserted.mappings().one()
    after = _leave_dict(row)
    await audit_log(session, _actor_id(user), "create", "leave_request", str(row["id"]), None, after)
    await session.commit()
    return {"data": {"id": after["id"], "days": len(requested_days), "status": "pending"}}


async def cancel_leave(session: AsyncSession, user: Any, leave_id: str) -> dict[str, Any]:
    """Cancel the caller's pending or future approved leave request."""
    employee_id = _own_employee_id(user)
    _, _, timezone_name = await _calendar_settings(session)
    today = _today(timezone_name)
    result = await session.execute(
        text(
            "SELECT id, employee_id, leave_type_id, start_date, end_date, days, reason, "
            "status, hr_comment, created_at FROM leave_requests "
            "WHERE id = CAST(:id AS uuid) AND employee_id = CAST(:employee_id AS uuid) "
            "FOR UPDATE"
        ),
        {"id": leave_id, "employee_id": employee_id},
    )
    row = result.mappings().first()
    if row is None:
        raise AppError(404, "leave_not_found", "The leave request was not found.")
    if row["status"] != "pending" and not (
        row["status"] == "approved" and row["start_date"] > today
    ):
        raise AppError(409, "leave_not_cancellable", "This leave request can no longer be cancelled.")

    before = _leave_dict(row)
    updated_result = await session.execute(
        text(
            "UPDATE leave_requests SET status = 'cancelled' WHERE id = CAST(:id AS uuid) "
            "RETURNING id, employee_id, leave_type_id, start_date, end_date, days, reason, "
            "status, hr_comment, created_at"
        ),
        {"id": leave_id},
    )
    updated = updated_result.mappings().one()
    after = _leave_dict(updated)
    await audit_log(session, _actor_id(user), "cancel", "leave_request", leave_id, before, after)
    await session.commit()
    return {"data": after}


async def list_leave(
    session: AsyncSession,
    user: Any,
    status: str | None = None,
    employee_id: str | None = None,
) -> dict[str, Any]:
    """List leave requests, forcing Employee callers to their own employee id."""
    own_id = scoped_employee_id(user)
    employee_filter = str(own_id) if own_id is not None else employee_id
    if status is not None and status not in {"pending", "approved", "rejected", "cancelled"}:
        raise AppError(400, "invalid_status", "The requested leave status is invalid.")
    result = await session.execute(
        text(
            "SELECT id, employee_id, leave_type_id, start_date, end_date, days, reason, "
            "status, hr_comment, created_at FROM leave_requests "
            "WHERE (:employee_id IS NULL OR employee_id = CAST(:employee_id AS uuid)) "
            "AND (:status IS NULL OR status = CAST(:status AS req_status)) "
            "ORDER BY created_at DESC"
        ),
        {"employee_id": employee_filter, "status": status},
    )
    return {"data": [_leave_dict(row) for row in result.mappings().all()]}


async def get_leave_balance(session: AsyncSession, user: Any) -> dict[str, Any]:
    """Compute this calendar year's approved usage and remaining leave balance."""
    employee_id = _own_employee_id(user)
    holidays, weekend, timezone_name = await _calendar_settings(session)
    year = _today(timezone_name).year
    types_result = await session.execute(
        text("SELECT id, name, yearly_quota FROM leave_types ORDER BY name")
    )
    balances = []
    for leave_type in types_result.mappings().all():
        used = await _approved_days_in_year(
            session, employee_id, str(leave_type["id"]), year, holidays, weekend
        )
        quota = leave_type["yearly_quota"]
        balances.append(
            {
                "leave_type_id": str(leave_type["id"]),
                "name": leave_type["name"],
                "quota": quota,
                "used": used,
                "remaining": leave_balance(quota, used),
            }
        )
    return {"data": balances}


async def decide_leave(
    session: AsyncSession,
    user: Any,
    leave_id: str,
    decision: str,
    comment: str | None = None,
) -> dict[str, Any]:
    """Approve or reject a pending leave request and notify its employee."""
    if decision not in {"approved", "rejected"}:
        raise AppError(400, "invalid_decision", "Decision must be approved or rejected.")
    if decision == "rejected" and not (comment and comment.strip()):
        raise AppError(400, "comment_required", "A comment is required when rejecting a leave request.")
    result = await session.execute(
        text(
            "SELECT id, employee_id, leave_type_id, start_date, end_date, days, reason, "
            "status, hr_comment, created_at FROM leave_requests "
            "WHERE id = CAST(:id AS uuid) FOR UPDATE"
        ),
        {"id": leave_id},
    )
    row = result.mappings().first()
    if row is None:
        raise AppError(404, "leave_not_found", "The leave request was not found.")
    if row["status"] != "pending":
        raise AppError(409, "leave_already_decided", "Only pending leave requests can be decided.")

    if decision == "approved":
        holidays, weekend, _ = await _calendar_settings(session)
        # Serialize applications and approvals for this employee while rechecking.
        await session.execute(
            text("SELECT id FROM employees WHERE id = :employee_id FOR UPDATE"),
            {"employee_id": row["employee_id"]},
        )
        conflict_result = await session.execute(
            text(
                "SELECT id, start_date, end_date FROM leave_requests "
                "WHERE employee_id = :employee_id AND id <> CAST(:id AS uuid) "
                "AND status IN ('pending', 'approved') "
                "AND start_date <= :end_date AND end_date >= :start_date"
            ),
            {
                "employee_id": row["employee_id"],
                "id": leave_id,
                "start_date": row["start_date"],
                "end_date": row["end_date"],
            },
        )
        if any(
            overlaps(row["start_date"], row["end_date"], conflict["start_date"], conflict["end_date"])
            for conflict in conflict_result.mappings().all()
        ):
            raise AppError(422, "overlap", "The request overlaps another pending or approved leave request.")

        type_result = await session.execute(
            text("SELECT yearly_quota FROM leave_types WHERE id = :leave_type_id"),
            {"leave_type_id": row["leave_type_id"]},
        )
        leave_type = type_result.mappings().first()
        if leave_type is None:
            raise AppError(404, "leave_type_not_found", "The selected leave type was not found.")
        quota = leave_type["yearly_quota"]
        if quota is not None:
            requested_days = working_days(
                row["start_date"], row["end_date"], holidays, weekend
            )
            if not requested_days:
                raise AppError(422, "no_working_days", "The request contains no working days under current settings.")
            for year in {day.year for day in requested_days}:
                requested_in_year = sum(day.year == year for day in requested_days)
                used = await _approved_days_in_year(
                    session,
                    str(row["employee_id"]),
                    str(row["leave_type_id"]),
                    year,
                    holidays,
                    weekend,
                )
                remaining = leave_balance(quota, used)
                if remaining is not None and requested_in_year > remaining:
                    raise AppError(422, "insufficient_balance", "The request exceeds the remaining leave balance.")

    before = _leave_dict(row)
    updated_result = await session.execute(
        text(
            "UPDATE leave_requests SET status = CAST(:decision AS req_status), "
            "hr_comment = :comment, decided_by = CAST(:actor_id AS uuid), decided_at = :now "
            "WHERE id = CAST(:id AS uuid) "
            "RETURNING id, employee_id, leave_type_id, start_date, end_date, days, reason, "
            "status, hr_comment, created_at"
        ),
        {
            "decision": decision,
            "comment": comment.strip() if comment else None,
            "actor_id": _actor_id(user),
            "now": datetime.now(timezone.utc),
            "id": leave_id,
        },
    )
    updated = updated_result.mappings().one()
    after = _leave_dict(updated)
    await audit_log(session, _actor_id(user), decision, "leave_request", leave_id, before, after)

    user_result = await session.execute(
        text("SELECT user_id FROM employees WHERE id = :employee_id"),
        {"employee_id": row["employee_id"]},
    )
    employee_user_id = user_result.scalar_one_or_none()
    if employee_user_id is not None:
        await notify(
            session,
            employee_user_id,
            f"Leave request {decision}",
            f"Your leave request for {row['start_date'].isoformat()} through "
            f"{row['end_date'].isoformat()} was {decision}.",
        )
    await session.commit()
    return {"data": after}


async def get_my_leave_balance(session: AsyncSession, user: Any) -> list[dict[str, Any]]:
    """Service alias for Abdullah's AI tools and employee dashboard."""
    result = await get_leave_balance(session, user)
    return result["data"]


async def get_leave_summary(
    session: AsyncSession,
    user: Any,
    from_date: date,
    to_date: date,
    department_id: str | None = None,
) -> dict[str, Any]:
    """Aggregate approved leave days and quota utilization by type and department."""
    if to_date < from_date:
        raise AppError(400, "invalid_date_range", "The end date must be on or after the start date.")
    holidays, weekend, _ = await _calendar_settings(session)
    own_id = scoped_employee_id(user)
    employee_filter = str(own_id) if own_id is not None else None
    request_result = await session.execute(
        text(
            "SELECT lr.employee_id, lr.start_date, lr.end_date, e.department_id, "
            "d.name AS department, lt.id AS leave_type_id, lt.name AS leave_type, "
            "lt.yearly_quota FROM leave_requests lr "
            "JOIN employees e ON e.id = lr.employee_id "
            "LEFT JOIN departments d ON d.id = e.department_id "
            "JOIN leave_types lt ON lt.id = lr.leave_type_id "
            "WHERE lr.status = 'approved' AND lr.start_date <= :to_date "
            "AND lr.end_date >= :from_date "
            "AND (:employee_id IS NULL OR lr.employee_id = CAST(:employee_id AS uuid)) "
            "AND (:department_id IS NULL OR e.department_id = CAST(:department_id AS uuid))"
        ),
        {
            "from_date": from_date,
            "to_date": to_date,
            "employee_id": employee_filter,
            "department_id": department_id,
        },
    )
    rows = request_result.mappings().all()

    department_filter = "AND e.department_id = CAST(:department_id AS uuid) " if department_id else ""
    employee_count_filter = (
        "AND e.id = CAST(:employee_id AS uuid) " if employee_filter else ""
    )
    headcount_result = await session.execute(
        text(
            "SELECT e.department_id, COUNT(*) AS headcount FROM employees e "
            "WHERE e.status IN ('active', 'probation') "
            + department_filter
            + employee_count_filter
            + "GROUP BY e.department_id"
        ),
        {"department_id": department_id, "employee_id": employee_filter},
    )
    headcounts = {
        str(row["department_id"]): row["headcount"]
        for row in headcount_result.mappings().all()
        if row["department_id"] is not None
    }

    type_groups: dict[str, dict[str, Any]] = {}
    dept_groups: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        start = max(row["start_date"], from_date)
        end = min(row["end_date"], to_date)
        approved_days = len(working_days(start, end, holidays, weekend))
        type_key = str(row["leave_type_id"])
        type_group = type_groups.setdefault(
            type_key,
            {
                "leave_type_id": type_key,
                "name": row["leave_type"],
                "approved_days": 0,
                "quota": row["yearly_quota"],
            },
        )
        type_group["approved_days"] += approved_days

        dep_key = str(row["department_id"]) if row["department_id"] else "unassigned"
        group_key = (dep_key, type_key)
        group = dept_groups.setdefault(
            group_key,
            {
                "department_id": row["department_id"],
                "department": row["department"] or "Unassigned",
                "leave_type_id": type_key,
                "leave_type": row["leave_type"],
                "approved_days": 0,
                "quota": row["yearly_quota"],
            },
        )
        group["approved_days"] += approved_days

    by_leave_type = []
    for group in type_groups.values():
        quota = group["quota"]
        eligible = sum(headcounts.values())
        total_quota = quota * eligible if quota is not None else None
        approved_days = group["approved_days"]
        by_leave_type.append(
            {
                "leave_type_id": group["leave_type_id"],
                "name": group["name"],
                "approved_days": approved_days,
                "quota": total_quota,
                "utilization": (
                    round(approved_days / total_quota * 100, 2)
                    if total_quota
                    else None
                ),
            }
        )

    by_department_leave_type = []
    department_totals: dict[str, dict[str, Any]] = {}
    for group in dept_groups.values():
        quota = group["quota"]
        total_quota = (
            quota * headcounts.get(str(group["department_id"]), 0)
            if quota is not None
            else None
        )
        approved_days = group["approved_days"]
        by_department_leave_type.append(
            {
                "department_id": str(group["department_id"])
                if group["department_id"]
                else None,
                "department": group["department"],
                "leave_type_id": group["leave_type_id"],
                "leave_type": group["leave_type"],
                "approved_days": approved_days,
                "quota": total_quota,
                "utilization": (
                    round(approved_days / total_quota * 100, 2)
                    if total_quota
                    else None
                ),
            }
        )

        department_key = str(group["department_id"]) if group["department_id"] else "unassigned"
        department = department_totals.setdefault(
            department_key,
            {
                "department_id": str(group["department_id"])
                if group["department_id"]
                else None,
                "department": group["department"],
                "approved_days": 0,
                "quota": 0,
                "unlimited": False,
            },
        )
        department["approved_days"] += approved_days
        if total_quota is None:
            department["unlimited"] = True
        else:
            department["quota"] += total_quota

    by_department = []
    for department in department_totals.values():
        quota = None if department.pop("unlimited") else department["quota"]
        department["quota"] = quota
        department["utilization"] = (
            round(department["approved_days"] / quota * 100, 2) if quota else None
        )
        by_department.append(department)

    return {
        "by_leave_type": by_leave_type,
        "by_department": by_department,
        "by_department_leave_type": by_department_leave_type,
    }
