from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_ENTITY_FIELDS = {
    "departments": ("name",),
    "designations": ("name",),
    "leave_types": ("name", "yearly_quota", "is_paid"),
    "holidays": ("date", "name"),
}
_ENTITY_ORDER = {"departments": "name", "designations": "name", "leave_types": "name", "holidays": "date"}


async def get_company_settings(session: AsyncSession) -> dict[str, Any] | None:
    result = await session.execute(text("SELECT * FROM settings WHERE id = 1"))
    row = result.mappings().one_or_none()
    return dict(row) if row else None


async def update_company_settings(
    session: AsyncSession, values: dict[str, Any]
) -> dict[str, Any] | None:
    assignments = ", ".join(f"{column} = :{column}" for column in values)
    result = await session.execute(
        text(f"UPDATE settings SET {assignments} WHERE id = 1 RETURNING *"),
        values,
    )
    row = result.mappings().one_or_none()
    return dict(row) if row else None


async def list_entities(
    session: AsyncSession, entity: str, page: int, page_size: int
) -> tuple[list[dict[str, Any]], int]:
    order_column = _ENTITY_ORDER[entity]
    count_result = await session.execute(text(f"SELECT count(*) FROM {entity}"))
    total = int(count_result.scalar_one())
    result = await session.execute(
        text(
            f"SELECT * FROM {entity} ORDER BY {order_column} "
            "LIMIT :limit OFFSET :offset"
        ),
        {"limit": page_size, "offset": (page - 1) * page_size},
    )
    return [dict(row) for row in result.mappings().all()], total


async def get_entity(
    session: AsyncSession, entity: str, entity_id: UUID
) -> dict[str, Any] | None:
    result = await session.execute(
        text(f"SELECT * FROM {entity} WHERE id = :entity_id"),
        {"entity_id": entity_id},
    )
    row = result.mappings().one_or_none()
    return dict(row) if row else None


async def create_entity(
    session: AsyncSession, entity: str, values: dict[str, Any]
) -> dict[str, Any]:
    fields = _ENTITY_FIELDS[entity]
    columns = ", ".join(fields)
    parameters = ", ".join(f":{field}" for field in fields)
    result = await session.execute(
        text(f"INSERT INTO {entity} ({columns}) VALUES ({parameters}) RETURNING *"),
        values,
    )
    return dict(result.mappings().one())


async def update_entity(
    session: AsyncSession,
    entity: str,
    entity_id: UUID,
    values: dict[str, Any],
) -> dict[str, Any] | None:
    fields = _ENTITY_FIELDS[entity]
    assignments = ", ".join(f"{field} = :{field}" for field in fields)
    result = await session.execute(
        text(
            f"UPDATE {entity} SET {assignments} "
            "WHERE id = :entity_id RETURNING *"
        ),
        {**values, "entity_id": entity_id},
    )
    row = result.mappings().one_or_none()
    return dict(row) if row else None


async def delete_entity(
    session: AsyncSession, entity: str, entity_id: UUID
) -> dict[str, Any] | None:
    result = await session.execute(
        text(f"DELETE FROM {entity} WHERE id = :entity_id RETURNING *"),
        {"entity_id": entity_id},
    )
    row = result.mappings().one_or_none()
    return dict(row) if row else None


async def insert_default_leave_type(
    session: AsyncSession,
    name: str,
    yearly_quota: int | None,
    is_paid: bool,
) -> dict[str, Any] | None:
    result = await session.execute(
        text(
            """
            INSERT INTO leave_types (name, yearly_quota, is_paid)
            VALUES (:name, :yearly_quota, :is_paid)
            ON CONFLICT (name) DO NOTHING
            RETURNING *
            """
        ),
        {"name": name, "yearly_quota": yearly_quota, "is_paid": is_paid},
    )
    row = result.mappings().one_or_none()
    return dict(row) if row else None


async def list_all_leave_types(session: AsyncSession) -> list[dict[str, Any]]:
    result = await session.execute(text("SELECT * FROM leave_types ORDER BY name"))
    return [dict(row) for row in result.mappings().all()]
