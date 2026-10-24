from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log as audit_log
from app.core.errors import AppError
from app.modules.settings import repo

_DEFAULT_LEAVE_TYPES = (
    {"name": "annual", "yearly_quota": 14, "is_paid": True},
    {"name": "sick", "yearly_quota": 8, "is_paid": True},
    {"name": "casual", "yearly_quota": 10, "is_paid": True},
    {"name": "unpaid", "yearly_quota": None, "is_paid": False},
)


def _db_error(exc: IntegrityError) -> AppError:
    code = getattr(getattr(exc, "orig", None), "sqlstate", None)
    if code == "23505":
        return AppError(409, "duplicate", "A record with these details already exists.")
    if code == "23503":
        return AppError(409, "in_use", "This record is referenced by other data.")
    if code == "23514":
        return AppError(422, "rule_violation", "The record violates a data rule.")
    return AppError(409, "data_conflict", "The change conflicts with existing data.")


async def _write(session: AsyncSession, result: Any) -> Any:
    try:
        await session.commit()
        return result
    except IntegrityError as exc:
        await session.rollback()
        raise _db_error(exc) from exc
    except Exception:
        await session.rollback()
        raise


async def get_settings(session: AsyncSession) -> dict[str, Any]:
    result = await repo.get_company_settings(session)
    if result is None:
        raise AppError(404, "not_found", "Company settings were not found.")
    return result


async def update_settings(session: AsyncSession, actor_id: UUID, values: dict[str, Any]) -> dict[str, Any]:
    before = await get_settings(session)
    after = await repo.update_company_settings(session, values)
    if after is None:
        raise AppError(404, "not_found", "Company settings were not found.")
    await audit_log(session, actor_id, "update", "settings", "1", before, after)
    return await _write(session, after)


async def list_entities(session: AsyncSession, entity: str, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    return await repo.list_entities(session, entity, page, page_size)


async def create_entity(session: AsyncSession, actor_id: UUID, entity: str, values: dict[str, Any]) -> dict[str, Any]:
    result = await repo.create_entity(session, entity, values)
    await audit_log(session, actor_id, "create", entity, result["id"], None, result)
    return await _write(session, result)


async def update_entity(session: AsyncSession, actor_id: UUID, entity: str, entity_id: UUID, values: dict[str, Any]) -> dict[str, Any]:
    before = await repo.get_entity(session, entity, entity_id)
    if before is None:
        raise AppError(404, "not_found", "The requested record was not found.")
    after = await repo.update_entity(session, entity, entity_id, values)
    if after is None:
        raise AppError(404, "not_found", "The requested record was not found.")
    await audit_log(session, actor_id, "update", entity, entity_id, before, after)
    return await _write(session, after)


async def delete_entity(session: AsyncSession, actor_id: UUID, entity: str, entity_id: UUID) -> None:
    before = await repo.delete_entity(session, entity, entity_id)
    if before is None:
        raise AppError(404, "not_found", "The requested record was not found.")
    await audit_log(session, actor_id, "delete", entity, entity_id, before, None)
    await _write(session, None)


async def add_default_leave_types(session: AsyncSession, actor_id: UUID) -> list[dict[str, Any]]:
    added = []
    try:
        for values in _DEFAULT_LEAVE_TYPES:
            result = await repo.insert_default_leave_type(session, **values)
            if result is not None:
                await audit_log(session, actor_id, "create", "leave_types", result["id"], None, result)
                added.append(result)
        await session.commit()
        return added
    except IntegrityError as exc:
        await session.rollback()
        raise _db_error(exc) from exc
    except Exception:
        await session.rollback()
        raise


async def list_leave_types(session: AsyncSession) -> list[dict[str, Any]]:
    return await repo.list_all_leave_types(session)
