from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log as audit_log
from app.core.config import get_settings
from app.core.errors import AppError
from app.modules.auth import repo as auth_repo


def _headers(key: str) -> dict[str, str]:
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


async def _admin_auth_request(method: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise AppError(503, "auth_not_configured", "Supabase Auth is not configured.")
    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/admin/users"
    if path:
        url = f"{url}/{path.lstrip('/')}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.request(
                method, url, headers=_headers(settings.supabase_service_role_key), json=payload
            )
    except httpx.HTTPError as exc:
        raise AppError(503, "auth_service_unavailable", "Supabase Auth is unavailable.") from exc
    if response.status_code in {400, 409, 422}:
        detail = response.text.lower()
        if "already" in detail or "exists" in detail or "registered" in detail:
            raise AppError(409, "duplicate_email", "An account with this email already exists.")
        raise AppError(400, "auth_user_invalid", "Supabase rejected the account details.")
    if response.status_code not in {200, 201}:
        raise AppError(503, "auth_service_error", "Supabase could not update the account.")
    return response.json()


async def list_users(session: AsyncSession) -> list[dict[str, Any]]:
    result = await session.execute(
        text(
            "SELECT p.id, u.email, p.role, p.is_active, p.must_change_password "
            "FROM profiles AS p JOIN auth.users AS u ON u.id = p.id "
            "ORDER BY p.created_at, u.email"
        )
    )
    return [dict(row) for row in result.mappings().all()]


async def create_hr_user(
    session: AsyncSession, actor_id: UUID, email: str, password: str
) -> dict[str, Any]:
    auth_user = await _admin_auth_request(
        "POST", "", {"email": email, "password": password, "email_confirm": True}
    )
    try:
        user_id = UUID(auth_user["id"])
        await auth_repo.insert_profile(session, user_id, "hr", must_change_password=True)
        await audit_log(
            session, actor_id, "create", "user", user_id, None,
            {"email": email, "role": "hr", "is_active": True},
        )
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        user_id = UUID(auth_user["id"])
        await _delete_auth_user(user_id)
        raise AppError(409, "duplicate_email", "An account with this email already exists.") from exc
    except Exception:
        await session.rollback()
        try:
            await _delete_auth_user(UUID(auth_user["id"]))
        except (KeyError, ValueError, TypeError):
            pass
        raise
    return {
        "id": str(user_id), "email": email, "role": "hr",
        "is_active": True, "must_change_password": True,
    }


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


async def set_active(
    session: AsyncSession, actor_id: UUID, user_id: UUID, is_active: bool
) -> dict[str, Any]:
    await session.execute(text("SELECT pg_advisory_xact_lock(72688302)"))
    result = await session.execute(
        text("SELECT id, role, is_active FROM profiles WHERE id = :user_id FOR UPDATE"),
        {"user_id": user_id},
    )
    row = result.mappings().one_or_none()
    if row is None:
        raise AppError(404, "user_not_found", "The user was not found.")
    if row["role"] == "admin" and not is_active:
        admins = await session.execute(text("SELECT count(*) FROM profiles WHERE role = 'admin' AND is_active"))
        if admins.scalar_one() <= 1:
            raise AppError(409, "last_admin", "The last active administrator cannot be disabled.")
    await session.execute(
        text("UPDATE profiles SET is_active = :is_active WHERE id = :user_id"),
        {"user_id": user_id, "is_active": is_active},
    )
    await audit_log(
        session, actor_id, "set_active", "user", user_id,
        {"is_active": row["is_active"]}, {"is_active": is_active},
    )
    await session.commit()
    return {"id": str(user_id), "is_active": is_active}


async def reset_password(
    session: AsyncSession, actor_id: UUID, user_id: UUID, password: str
) -> dict[str, Any]:
    result = await session.execute(
        text("SELECT id FROM profiles WHERE id = :user_id"), {"user_id": user_id}
    )
    if result.scalar_one_or_none() is None:
        raise AppError(404, "user_not_found", "The user was not found.")
    await _admin_auth_request("PUT", str(user_id), {"password": password})
    await session.execute(
        text("UPDATE profiles SET must_change_password = true WHERE id = :user_id"),
        {"user_id": user_id},
    )
    await audit_log(
        session, actor_id, "reset_password", "user", user_id,
        None, {"must_change_password": True},
    )
    await session.commit()
    return {"id": str(user_id), "must_change_password": True}
