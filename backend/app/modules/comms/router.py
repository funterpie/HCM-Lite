from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_role
from app.db import get_session
from app.modules.comms import service
from app.modules.comms.schemas import AnnouncementCreate

router = APIRouter(tags=["comms"])


@router.get("/announcements")
async def get_announcements(
    _: CurrentUser = Depends(require_role("admin", "hr", "employee")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await service.list_announcements(session)


@router.post("/announcements", status_code=201)
async def create_announcement(
    payload: AnnouncementCreate,
    user: CurrentUser = Depends(require_role("admin", "hr")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await service.post_announcement(session, user.id, payload.title, payload.body)


@router.get("/notifications")
async def get_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: CurrentUser = Depends(require_role("admin", "hr", "employee")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await service.list_notifications(session, user.id, page, page_size)


@router.patch("/notifications/{notification_id}/read")
async def read_notification(
    notification_id: UUID,
    user: CurrentUser = Depends(require_role("admin", "hr", "employee")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await service.mark_notification_read(session, user.id, notification_id)


@router.get("/audit")
async def get_audit(
    actor: UUID | None = None,
    entity: str | None = Query(default=None, min_length=1, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    _: CurrentUser = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await service.list_audit(session, actor, entity, page, page_size)
