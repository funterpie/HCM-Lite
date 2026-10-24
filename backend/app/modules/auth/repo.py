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
