from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

async def log(session: AsyncSession, actor: str, action: str, entity: str, before: dict = None, after: dict = None):
    """Append-only audit log entry."""
    try:
        query = text("""
            INSERT INTO audit_logs (actor, action, entity, before_state, after_state, created_at)
            VALUES (:actor, :action, :entity, :before::jsonb, :after::jsonb, NOW())
        """)
        await session.execute(query, {
            "actor": actor,
            "action": action,
            "entity": entity,
            "before": str(before) if before else None,
            "after": str(after) if after else None
        })
        await session.commit()
    except Exception as e:
        logger.error(f"Audit log failed: {e}")
