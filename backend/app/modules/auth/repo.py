from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_profile_for_user(session: AsyncSession, user_id: UUID) -> dict[str, Any] | None:
    result = await session.execute(
        text(
            """
            SELECT id, role, is_active, must_change_password
            FROM profiles
            WHERE id = :user_id
            """
        ),
        {"user_id": user_id},
    )
    row = result.mappings().one_or_none()
    return dict(row) if row else None


async def get_employee_id_for_user(session: AsyncSession, user_id: UUID) -> UUID | None:
    result = await session.execute(
        text("SELECT id FROM employees WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    return result.scalar_one_or_none()


async def needs_setup(session: AsyncSession) -> bool:
    result = await session.execute(text("SELECT NOT EXISTS (SELECT 1 FROM settings)"))
    return bool(result.scalar_one())


async def claim_setup(
    session: AsyncSession, company_name: str, timezone: str = "Asia/Karachi"
) -> bool:
    result = await session.execute(
        text(
            """
            INSERT INTO settings (id, company_name, timezone)
            VALUES (1, :company_name, :timezone)
            ON CONFLICT (id) DO NOTHING
            RETURNING id
            """
        ),
        {"company_name": company_name, "timezone": timezone},
    )
    return result.scalar_one_or_none() is not None


async def insert_profile(
    session: AsyncSession,
    user_id: UUID,
    role: str,
    must_change_password: bool = False,
) -> None:
    await session.execute(
        text(
            """
            INSERT INTO profiles (id, role, must_change_password, is_active)
            VALUES (:user_id, :role, :must_change_password, true)
            """
        ),
        {
            "user_id": user_id,
            "role": role,
            "must_change_password": must_change_password,
        },
    )


async def set_must_change_password(
    session: AsyncSession, user_id: UUID, value: bool
) -> None:
    await session.execute(
        text(
            """
            UPDATE profiles
            SET must_change_password = :value
            WHERE id = :user_id
            """
        ),
        {"value": value, "user_id": user_id},
    )


async def acquire_admin_bootstrap_lock(session: AsyncSession) -> None:
    await session.execute(text("SELECT pg_advisory_xact_lock(72688301)"))


async def settings_exist(session: AsyncSession) -> bool:
    result = await session.execute(text("SELECT EXISTS (SELECT 1 FROM settings)"))
    return bool(result.scalar_one())


async def admin_profile_exists(session: AsyncSession) -> bool:
    result = await session.execute(
        text("SELECT EXISTS (SELECT 1 FROM profiles WHERE role = 'admin')")
    )
    return bool(result.scalar_one())
