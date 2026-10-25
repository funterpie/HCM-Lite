from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log as audit_log
from app.core.config import get_settings
from app.core.deps import CurrentUser
from app.core.errors import AppError
from app.db import SessionLocal
from app.modules.auth import repo


def _admin_api_headers(service_role_key: str) -> dict[str, str]:
    return {
        "apikey": service_role_key,
        "Authorization": f"Bearer {service_role_key}",
        "Content-Type": "application/json",
    }


async def _create_auth_user(email: str, password: str) -> UUID:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise AppError(503, "auth_not_configured", "Supabase Auth is not configured.")

    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/admin/users"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                headers=_admin_api_headers(settings.supabase_service_role_key),
                json={"email": email, "password": password, "email_confirm": True},
            )
    except httpx.HTTPError as exc:
        raise AppError(503, "auth_service_unavailable", "Supabase Auth is unavailable.") from exc

    if response.status_code in {400, 409, 422}:
        detail = response.text.lower()
        if "already" in detail or "exists" in detail or "registered" in detail:
            raise AppError(409, "duplicate_email", "An account with this email already exists.")
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
    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/admin/users/{user_id}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.delete(url, headers=_admin_api_headers(settings.supabase_service_role_key))
    except httpx.HTTPError:
        return


async def get_setup_status(session: AsyncSession) -> dict[str, bool]:
    return {"needs_setup": await repo.needs_setup(session)}


async def setup_company(
    session: AsyncSession, company_name: str, admin_email: str, admin_password: str
) -> dict[str, str]:
    admin_id: UUID | None = None
    try:
        if not await repo.claim_setup(session, company_name):
            raise AppError(409, "already_setup", "Initial setup has already been completed.")

        admin_id = await _create_auth_user(admin_email, admin_password)
        await repo.insert_profile(session, admin_id, "admin")
        await audit_log(
            session,
            actor_id=admin_id,
            action="setup",
            entity="settings",
            entity_id="1",
            before=None,
            after={"company_name": company_name, "admin_email": admin_email},
        )
        await session.commit()
    except Exception:
        await session.rollback()
        if admin_id is not None:
            await _delete_auth_user(admin_id)
        raise

    return {
        "admin_id": str(admin_id),
        "admin_email": admin_email,
        "company_name": company_name,
    }


async def get_me(user: CurrentUser) -> dict[str, str | bool | None]:
    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role,
        "employee_id": str(user.employee_id) if user.employee_id else None,
        "must_change_password": user.must_change_password,
    }


async def change_password(
    session: AsyncSession, user: CurrentUser, new_password: str
) -> None:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise AppError(503, "auth_not_configured", "Supabase Auth is not configured.")

    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/admin/users/{user.id}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.put(
                url,
                headers=_admin_api_headers(settings.supabase_service_role_key),
                json={"password": new_password},
            )
    except httpx.HTTPError as exc:
        raise AppError(503, "auth_service_unavailable", "Supabase Auth is unavailable.") from exc

    if response.status_code not in {200, 201}:
        raise AppError(400, "password_update_failed", "Supabase could not update the password.")

    try:
        await repo.set_must_change_password(session, user.id, False)
        await audit_log(
            session,
            actor_id=user.id,
            action="change_password",
            entity="profile",
            entity_id=str(user.id),
            before={"must_change_password": user.must_change_password},
            after={"must_change_password": False},
        )
        await session.commit()
    except Exception:
        await session.rollback()
        raise


async def ensure_configured_admin() -> None:
    settings = get_settings()
    if not settings.admin_email or not settings.admin_password:
        return
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is required when ADMIN_EMAIL and ADMIN_PASSWORD are configured")

    async with SessionLocal() as session:
        admin_id: UUID | None = None
        try:
            await repo.acquire_admin_bootstrap_lock(session)
            if not await repo.settings_exist(session) or await repo.admin_profile_exists(session):
                await session.rollback()
                return
            admin_id = await _create_auth_user(settings.admin_email, settings.admin_password)
            await repo.insert_profile(session, admin_id, "admin")
            await audit_log(
                session,
                actor_id=admin_id,
                action="bootstrap_admin",
                entity="profile",
                entity_id=str(admin_id),
                before=None,
                after={"role": "admin", "email": settings.admin_email},
            )
            await session.commit()
        except Exception:
            await session.rollback()
            if admin_id is not None:
                await _delete_auth_user(admin_id)
            raise
