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


def _own_employee_id(user: Any) -> str:
    value = _value(user, "employee_id")
    if value is None:
        raise AppError(403, "employee_record_required")
    return str(value)


def _actor_id(user: Any) -> str:
    value = _value(user, "id")
    if value is None:
        raise AppError(401, "unauthenticated")
    return str(value)


async def _calendar_settings(session: AsyncSession) -> tuple[set[date], set[int], str]:
    result = await session.execute(
        text("SELECT timezone, weekend_days FROM settings WHERE id = 1")
    )
    row = result.mappings().first()
    if row is None:
        raise AppError(400, "settings_not_configured")
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
        raise AppError(400, "invalid_date_range")
    employee_id = _own_employee_id(user)
    holidays, weekend, _ = await _calendar_settings(session)
    requested_days = working_days(start_date, end_date, holidays, weekend)
    if not requested_days:
        raise AppError(422, "no_working_days")

    type_result = await session.execute(
        text("SELECT id, yearly_quota FROM leave_types WHERE id = CAST(:id AS uuid)"),
        {"id": leave_type_id},
    )
    leave_type = type_result.mappings().first()
    if leave_type is None:
        raise AppError(404, "leave_type_not_found")

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
        raise AppError(422, "overlap")

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
                raise AppError(422, "insufficient_balance")

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
    await audit_log(session, user, "create", "leave_request", str(row["id"]), None, after)
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
        raise AppError(404, "leave_not_found")
    if row["status"] != "pending" and not (
        row["status"] == "approved" and row["start_date"] > today
    ):
        raise AppError(409, "leave_not_cancellable")

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
    await audit_log(session, user, "cancel", "leave_request", leave_id, before, after)
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
        raise AppError(400, "invalid_status")
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
        raise AppError(400, "invalid_decision")
    if decision == "rejected" and not (comment and comment.strip()):
        raise AppError(400, "comment_required")
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
        raise AppError(404, "leave_not_found")
    if row["status"] != "pending":
        raise AppError(409, "leave_already_decided")

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
    await audit_log(session, user, f"{decision}", "leave_request", leave_id, before, after)

    user_result = await session.execute(
        text("SELECT user_id FROM employees WHERE id = :employee_id"),
        {"employee_id": row["employee_id"]},
    )
    employee_user_id = user_result.scalar_one_or_none()
    if employee_user_id is not None:
        await notify(
            session,
            str(employee_user_id),
            f"Leave request {decision}",
            f"Your leave request for {row['start_date'].isoformat()} through "
            f"{row['end_date'].isoformat()} was {decision}.",
        )
    await session.commit()
    return {"data": after}
