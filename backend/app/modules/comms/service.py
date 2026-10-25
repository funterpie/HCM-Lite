from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log as audit_log
from app.core.errors import AppError
from app.modules.comms import repo


async def list_announcements(session: AsyncSession) -> dict[str, Any]:
    return {"data": await repo.list_announcements(session)}


async def post_announcement(
    session: AsyncSession, actor_id: UUID, title: str, body: str
) -> dict[str, Any]:
    item = await repo.create_announcement(session, actor_id, title.strip(), body.strip())
    await audit_log(session, actor_id, "create", "announcement", item["id"], None, item)
    await session.commit()
    return {"data": item}


async def list_notifications(
    session: AsyncSession, user_id: UUID, page: int, page_size: int
) -> dict[str, Any]:
    items, unread_count = await repo.list_notifications(session, user_id, page, page_size)
    return {
        "data": items,
        "meta": {"page": page, "page_size": page_size, "unread_count": unread_count},
    }


async def mark_notification_read(
    session: AsyncSession, user_id: UUID, notification_id: UUID
) -> dict[str, Any]:
    item = await repo.mark_notification_read(session, user_id, notification_id)
    if item is None:
        raise AppError(404, "notification_not_found", "The notification was not found.")
    await session.commit()
    return {"data": item}


async def list_audit(
    session: AsyncSession,
    actor_id: UUID | None,
    entity: str | None,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    records, total = await repo.list_audit(session, actor_id, entity, page, page_size)
    return {
        "data": records,
        "meta": {"page": page, "page_size": page_size, "total": total},
    }
