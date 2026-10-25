from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repo import count_user_ai_logs_last_hour, insert_ai_log


async def log_ai_call(
    session: AsyncSession,
    user_id: UUID | None,
    kind: str,
    prompt: str,
    tool: str | None,
    response: str | None,
    latency_ms: int | None,
    ok: bool,
) -> None:
    await insert_ai_log(
        session, user_id, kind, prompt, tool, response, latency_ms, ok
    )


async def count_ai_calls_last_hour(session: AsyncSession, user_id: UUID) -> int:
    return await count_user_ai_logs_last_hour(session, user_id)
