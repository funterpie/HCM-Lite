from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def list_announcements(session: AsyncSession) -> list[dict[str, Any]]:
    result = await session.execute(
        text(
            "SELECT a.id, a.title, a.body, a.posted_by, u.email AS posted_by_email, a.created_at "
            "FROM announcements AS a LEFT JOIN auth.users AS u ON u.id = a.posted_by "
            "ORDER BY a.created_at DESC LIMIT 100"
        )
    )
    return [dict(row) for row in result.mappings().all()]


async def create_announcement(
    session: AsyncSession, actor_id: UUID, title: str, body: str
) -> dict[str, Any]:
    result = await session.execute(
        text(
            "INSERT INTO announcements (title, body, posted_by) "
            "VALUES (:title, :body, :posted_by) RETURNING id, title, body, posted_by, created_at"
        ),
        {"title": title, "body": body, "posted_by": actor_id},
    )
    return dict(result.mappings().one())


async def list_notifications(
    session: AsyncSession, user_id: UUID, page: int, page_size: int
) -> tuple[list[dict[str, Any]], int]:
    rows = await session.execute(
        text(
            "SELECT id, title, body, read, created_at FROM notifications "
            "WHERE user_id = :user_id ORDER BY created_at DESC "
            "LIMIT :limit OFFSET :offset"
        ),
        {"user_id": user_id, "limit": page_size, "offset": (page - 1) * page_size},
    )
    unread = await session.execute(
        text("SELECT count(*)::integer FROM notifications WHERE user_id = :user_id AND read = false"),
        {"user_id": user_id},
    )
    return [dict(row) for row in rows.mappings().all()], int(unread.scalar_one())


async def mark_notification_read(
    session: AsyncSession, user_id: UUID, notification_id: UUID
) -> dict[str, Any] | None:
    result = await session.execute(
        text(
            "UPDATE notifications SET read = true WHERE id = :notification_id "
            "AND user_id = :user_id RETURNING id, title, body, read, created_at"
        ),
        {"notification_id": notification_id, "user_id": user_id},
    )
    row = result.mappings().one_or_none()
    return dict(row) if row else None


async def list_audit(
    session: AsyncSession,
    actor_id: UUID | None,
    entity: str | None,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    params = {
        "actor_id": actor_id,
        "entity": entity,
        "limit": page_size,
        "offset": (page - 1) * page_size,
    }
    where = (
        "WHERE (CAST(:actor_id AS uuid) IS NULL OR a.actor_id = CAST(:actor_id AS uuid)) "
        "AND (CAST(:entity AS text) IS NULL OR a.entity = CAST(:entity AS text))"
    )
    total_result = await session.execute(
        text(f"SELECT count(*) FROM audit_logs AS a {where}"), params
    )
    result = await session.execute(
        text(
            "SELECT a.id, a.actor_id, u.email AS actor_email, a.action, a.entity, "
            "a.entity_id, a.\"before\", a.\"after\", a.created_at "
            f"FROM audit_logs AS a LEFT JOIN auth.users AS u ON u.id = a.actor_id {where} "
            "ORDER BY a.created_at DESC, a.id DESC LIMIT :limit OFFSET :offset"
        ),
        params,
    )
    return [dict(row) for row in result.mappings().all()], int(total_result.scalar_one())
