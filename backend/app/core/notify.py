from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repo import insert_notification


async def notify(session: AsyncSession, user_id: UUID, title: str, body: str) -> None:
    await insert_notification(session, user_id, title, body)
