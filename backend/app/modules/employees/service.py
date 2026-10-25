from datetime import date
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log as audit_log
from app.core.config import get_settings
from app.core.deps import CurrentUser
from app.core.errors import AppError
from app.core.notify import notify
from app.modules.attendance.service import get_attendance_summary
from app.modules.employees import repo
from app.modules.leave.service import get_leave_balance


def _headers(key: str) -> dict[str, str]:
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


async def _create_auth_user(email: str, password: str) -> UUID:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise AppError(503, "auth_not_configured", "Supabase Auth is not configured.")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.supabase_url.rstrip('/')}/auth/v1/admin/users",
                headers=_headers(settings.supabase_service_role_key),
                json={"email": email, "password": password, "email_confirm": True},
            )
    except httpx.HTTPError as exc:
        raise AppError(503, "auth_service_unavailable", "Supabase Auth is unavailable.") from exc
    if response.status_code in {400, 409, 422}:
        detail = response.text.lower()
        if "already" in detail or "exists" in detail or "registered" in detail:
            raise AppError(409, "duplicate_email", "An account with this email already exists.", {"email": "already in use"})
        raise AppError(400, "auth_user_invalid", "Supabase rejected the account details.")
    if response.status_code not in {200, 201}:
        raise AppError(503, "auth_service_error", "Supabase could not create the account.")
    try:
        return UUID(response.json()["id"])
    except (ValueError, KeyError, TypeError) as exc:
        raise AppError(503, "auth_service_error", "Supabase returned an invalid account response.") from exc


async def _delete_auth_user(user_id: UUID) -> None:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        return
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.delete(
                f"{settings.supabase_url.rstrip('/')}/auth/v1/admin/users/{user_id}",
                headers=_headers(settings.supabase_service_role_key),
            )
    except httpx.HTTPError:
        return


def _integrity_error(exc: IntegrityError) -> AppError:
    name = getattr(getattr(getattr(exc, "orig", None), "diag", None), "constraint_name", "") or ""
    if "email" in name:
        return AppError(409, "duplicate_email", "An account with this email already exists.", {"email": "already in use"})
    if "code" in name:
        return AppError(409, "duplicate_code", "An employee with this code already exists.", {"code": "already in use"})
    if "department" in name:
        return AppError(422, "invalid_department", "The selected department does not exist.", {"department_id": "unknown department"})
    if "designation" in name:
        return AppError(422, "invalid_designation", "The selected designation does not exist.", {"designation_id": "unknown designation"})
    return AppError(409, "data_conflict", "The employee change conflicts with existing data.")


async def _commit(session: AsyncSession, value: Any) -> Any:
    try:
        await session.commit()
        return value
    except IntegrityError as exc:
        await session.rollback()
        raise _integrity_error(exc) from exc
    except Exception:
        await session.rollback()
        raise


async def _validate_org_refs(session: AsyncSession, data: dict[str, Any]) -> None:
    department_id = data.get("department_id")
    if department_id is not None and not await repo.department_exists(session, department_id):
        raise AppError(422, "invalid_department", "The selected department does not exist.", {"department_id": "unknown department"})
    designation_id = data.get("designation_id")
    if designation_id is not None and not await repo.designation_exists(session, designation_id):
        raise AppError(422, "invalid_designation", "The selected designation does not exist.", {"designation_id": "unknown designation"})


async def create_employee_for_user(
    session: AsyncSession,
    user_id: UUID,
    data: dict[str, Any],
    role: str = "employee",
    actor_id: UUID | None = None,
) -> dict[str, Any]:
    if role not in {"employee", "hr"}:
        raise AppError(422, "invalid_role", "Employee accounts can only use employee or HR roles.")
    await _validate_org_refs(session, data)
    await repo.create_profile(session, user_id, role)
    result = await repo.create_employee(session, user_id, data)
    await audit_log(session, actor_id, "create", "employee", result["id"], None, result)
    await notify(session, user_id, "Welcome to HCM Lite", "Your company account is ready. Sign in and change your temporary password.")
    return result


async def create_employee(session: AsyncSession, actor_id: UUID, values: dict[str, Any], password: str) -> dict[str, Any]:
    user_id = await _create_auth_user(values["email"], password)
    employee_data = {key: value for key, value in values.items() if key != "temp_password"}
    try:
        result = await create_employee_for_user(session, user_id, employee_data, actor_id=actor_id)
        await session.commit()
        return result
    except IntegrityError as exc:
        await session.rollback()
        await _delete_auth_user(user_id)
        raise _integrity_error(exc) from exc
    except Exception:
        await session.rollback()
        await _delete_auth_user(user_id)
        raise


async def list_employees(
    session: AsyncSession,
    query: str | None,
    department_id: UUID | None,
    employee_status: str | None,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    return await repo.list_employees(session, query, department_id, employee_status, page, page_size)


async def get_employee(session: AsyncSession, employee_id: UUID) -> dict[str, Any]:
    result = await repo.get_employee(session, employee_id)
    if result is None:
        raise AppError(404, "not_found", "The employee was not found.")
    profile = {key: result.get(key) for key in (
        "id", "user_id", "code", "email", "full_name", "phone", "address", "gender",
        "department_id", "department", "designation_id", "designation", "join_date", "exit_date",
        "status", "basic_salary", "role", "is_active", "must_change_password",
    )}
    attendance_summary: dict[str, Any] = {}
    leave_balances: list[dict[str, Any]] = []
    if result["user_id"] is not None:
        employee_user = CurrentUser(
            id=result["user_id"], role="employee", is_active=True,
            must_change_password=False, employee_id=result["id"],
        )
        through = date.today()
        attendance_summary = await get_attendance_summary(
            session, employee_user, result["join_date"], through
        )
        leave_result = await get_leave_balance(session, employee_user)
        leave_balances = leave_result["data"]
    return {
        "profile": profile,
        "attendance_summary": attendance_summary,
        "leave_balances": leave_balances,
        "last_payslip": await repo.employee_360_last_payslip(session, employee_id),
    }


async def update_employee(
    session: AsyncSession, actor_id: UUID, employee_id: UUID, values: dict[str, Any]
) -> dict[str, Any]:
    before = await repo.get_employee(session, employee_id)
    if before is None:
        raise AppError(404, "not_found", "The employee was not found.")
    await _validate_org_refs(session, values)
    after = await repo.update_employee(session, employee_id, values)
    if after is None:
        raise AppError(404, "not_found", "The employee was not found.")
    await audit_log(session, actor_id, "update", "employee", employee_id, before, after)
    return await _commit(session, after)


async def update_my_profile(
    session: AsyncSession, user_id: UUID, values: dict[str, Any]
) -> dict[str, Any]:
    before = await repo.get_employee_by_user(session, user_id)
    if before is None:
        raise AppError(404, "not_found", "No employee record is linked to this account.")
    after = await repo.update_profile_fields(session, user_id, values)
    if after is None:
        raise AppError(404, "not_found", "No employee record is linked to this account.")
    await audit_log(session, user_id, "update", "employee_profile", after["id"], before, after)
    return await _commit(session, after)


async def update_salary(
    session: AsyncSession, actor_id: UUID, employee_id: UUID, basic_salary: Any
) -> dict[str, Any]:
    before = await repo.get_employee(session, employee_id)
    if before is None:
        raise AppError(404, "not_found", "The employee was not found.")
    after = await repo.set_salary(session, employee_id, basic_salary)
    if after is None:
        raise AppError(404, "not_found", "The employee was not found.")
    await audit_log(session, actor_id, "update_salary", "employee", employee_id, {"basic_salary": before["basic_salary"]}, after)
    return await _commit(session, after)
