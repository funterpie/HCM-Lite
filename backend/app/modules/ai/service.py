import json
import time
from datetime import date
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import CurrentUser
from app.core.errors import AppError
from app.core.repo import count_user_ai_logs_last_hour, insert_ai_log
from app.modules.dashboards import service as dashboard_service
from app.modules.settings import repo as settings_repo

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


async def _complete(
    session: AsyncSession,
    user: CurrentUser,
    kind: str,
    prompt: str,
    system: str,
    *,
    json_mode: bool = False,
) -> str:
    settings = get_settings()
    if not settings.ai_api_key:
        raise AppError(503, "ai_not_configured", "AI is not configured. Set AI_API_KEY on the backend to enable this feature.")
    if await count_user_ai_logs_last_hour(session, user.id) >= 20:
        raise AppError(429, "rate_limited", "The AI request limit has been reached. Try again later.")
    messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
    payload: dict[str, Any] = {
        "model": settings.ai_model or "openai/gpt-oss-120b",
        "messages": messages,
        "temperature": 0.1,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    started = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.post(
                _GROQ_URL,
                headers={"Authorization": f"Bearer {settings.ai_api_key}"},
                json=payload,
            )
    except httpx.HTTPError as exc:
        raise AppError(503, "ai_unavailable", "The AI provider could not be reached.") from exc
    if response.status_code == 429:
        raise AppError(429, "rate_limited", "The AI provider is rate limiting requests. Try again shortly.")
    if response.status_code != 200:
        raise AppError(503, "ai_provider_error", "The AI provider rejected the request. Check the backend AI configuration.")
    try:
        answer = response.json()["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise AppError(502, "ai_invalid_response", "The AI provider returned an invalid response.") from exc
    if not isinstance(answer, str) or not answer.strip():
        raise AppError(502, "ai_invalid_response", "The AI provider returned an empty response.")
    await insert_ai_log(
        session, user.id, kind, prompt[:2000], None, answer[:8000],
        int((time.monotonic() - started) * 1000), True,
    )
    await session.commit()
    return answer.strip()


def _ai_system_context(role: str) -> str:
    return (
        "You are HCM Lite's assistant. Use only the supplied company context; never invent facts, "
        "metrics, policies, or dates. If context is insufficient, say so. Employee users may only "
        "receive their own personal data; refuse requests for colleagues' salaries or private data. "
        "For admin and HR, answer only from the operational context supplied and do not infer individual "
        "payroll or private information. Clearly state uncertainty. Role: " + role + "."
    )


async def chat(session: AsyncSession, user: CurrentUser, message: str, history: list[dict[str, str]]) -> dict[str, str]:
    if user.role in {"admin", "hr"}:
        dashboard = await dashboard_service.get_hr_dashboard(session, None, None, None)
        context = dashboard["data"]
        if user.role == "admin":
            context = await dashboard_service.get_admin_dashboard(session, None, None, None)
    elif user.role == "employee":
        context = (await dashboard_service.get_me_dashboard(session, user))["data"]
    else:
        raise AppError(403, "forbidden", "You do not have permission to use the AI assistant.")
    prompt = json.dumps({"context": context, "history": history[-10:], "question": message}, default=str)
    answer = await _complete(session, user, "chat", prompt, _ai_system_context(user.role))
    return {"answer": answer, "tool_used": "scoped_live_context"}


async def summarize(
    session: AsyncSession,
    user: CurrentUser,
    dashboard: str,
    from_date: date | None,
    to_date: date | None,
    department_id: UUID | None,
) -> dict[str, list[str]]:
    if dashboard == "admin":
        if user.role != "admin":
            raise AppError(403, "forbidden", "Only admins can summarize the executive dashboard.")
        data = await dashboard_service.get_admin_dashboard(session, from_date, to_date, str(department_id) if department_id else None)
    else:
        if user.role not in {"admin", "hr"}:
            raise AppError(403, "forbidden", "Only admins and HR can summarize the HR dashboard.")
        data = await dashboard_service.get_hr_dashboard(session, from_date, to_date, str(department_id) if department_id else None)
    raw = await _complete(
        session, user, "summary", json.dumps(data, default=str),
        "Summarize only the supplied dashboard data. Return a JSON object with a bullets array of 3 to 5 concise, factual strings. Do not infer missing values.",
        json_mode=True,
    )
    try:
        bullets = json.loads(raw).get("bullets")
    except (json.JSONDecodeError, AttributeError) as exc:
        raise AppError(502, "ai_invalid_response", "The AI summary was not valid JSON.") from exc
    if not isinstance(bullets, list) or not all(isinstance(item, str) for item in bullets):
        raise AppError(502, "ai_invalid_response", "The AI summary did not include valid bullets.")
    return {"bullets": bullets[:5]}


async def smart_leave(session: AsyncSession, user: CurrentUser, text: str) -> dict[str, Any]:
    if user.role not in {"employee", "hr"}:
        raise AppError(403, "forbidden", "Only employees and HR can use Smart Leave.")
    types, _ = await settings_repo.list_entities(session, "leave_types", 1, 100)
    if not types:
        raise AppError(400, "leave_types_missing", "Configure at least one leave type before using Smart Leave.")
    choices = [{"id": str(item["id"]), "name": item["name"]} for item in types]
    prompt = json.dumps({"request": text, "today": date.today().isoformat(), "leave_types": choices})
    raw = await _complete(
        session, user, "smart_leave", prompt,
        "Interpret the leave request. Return JSON with leave_type_id, start_date, end_date, reason. "
        "Use an ID from the provided leave types. Use ISO dates. Never submit or save the request.",
        json_mode=True,
    )
    try:
        result = json.loads(raw)
        leave_type_id = UUID(result["leave_type_id"])
        start_date = date.fromisoformat(result["start_date"])
        end_date = date.fromisoformat(result["end_date"])
        reason = str(result.get("reason") or text)[:500]
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise AppError(502, "ai_invalid_response", "The AI could not produce a valid leave draft.") from exc
    if str(leave_type_id) not in {item["id"] for item in choices} or end_date < start_date:
        raise AppError(502, "ai_invalid_response", "The AI returned an invalid leave type or date range.")
    selected = next(item for item in choices if item["id"] == str(leave_type_id))
    return {
        "leave_type_id": str(leave_type_id), "leave_type_name": selected["name"],
        "start_date": start_date.isoformat(), "end_date": end_date.isoformat(), "reason": reason,
    }
