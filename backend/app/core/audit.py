from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repo import insert_audit_log


async def log(
    session: AsyncSession,
    actor_id: UUID | None,
    action: str,
    entity: str,
    entity_id: str | UUID | None,
    before: Any = None,
    after: Any = None,
) -> None:
    await insert_audit_log(
        session,
        actor_id,
        action,
        entity,
        str(entity_id) if entity_id is not None else None,
        before,
        after,
    )
