from typing import Any
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import bindparam, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession


async def insert_audit_log(
    session: AsyncSession,
    actor_id: UUID | None,
    action: str,
    entity: str,
    entity_id: str | None,
    before: Any,
    after: Any,
) -> None:
    statement = text(
        """
        INSERT INTO audit_logs (actor_id, action, entity, entity_id, "before", "after")
        VALUES (:actor_id, :action, :entity, :entity_id, :before_data, :after_data)
        """
    ).bindparams(
        bindparam("before_data", type_=JSONB),
        bindparam("after_data", type_=JSONB),
    )
    await session.execute(
        statement,
        {
            "actor_id": actor_id,
            "action": action,
            "entity": entity,
            "entity_id": entity_id,
            "before_data": jsonable_encoder(before),
            "after_data": jsonable_encoder(after),
        },
    )


async def insert_notification(
    session: AsyncSession, user_id: UUID, title: str, body: str
) -> None:
    await session.execute(
        text(
            """
            INSERT INTO notifications (user_id, title, body)
            VALUES (:user_id, :title, :body)
            """
        ),
        {"user_id": user_id, "title": title, "body": body},
    )


async def insert_ai_log(
    session: AsyncSession,
    user_id: UUID | None,
    kind: str,
    prompt: str,
    tool: str | None,
    response: str | None,
    latency_ms: int | None,
    ok: bool,
) -> None:
    await session.execute(
        text(
            """
            INSERT INTO ai_logs (user_id, kind, prompt, tool, response, latency_ms, ok)
            VALUES (:user_id, :kind, :prompt, :tool, :response, :latency_ms, :ok)
            """
        ),
        {
            "user_id": user_id,
            "kind": kind,
            "prompt": prompt,
            "tool": tool,
            "response": response,
            "latency_ms": latency_ms,
            "ok": ok,
        },
    )


async def count_user_ai_logs_last_hour(session: AsyncSession, user_id: UUID) -> int:
    result = await session.execute(
        text(
            """
            SELECT count(*)
            FROM ai_logs
            WHERE user_id = :user_id
              AND created_at >= now() - interval '1 hour'
            """
        ),
        {"user_id": user_id},
    )
    return int(result.scalar_one())
