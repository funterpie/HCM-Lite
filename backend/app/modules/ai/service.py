import os
import httpx
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.modules.ai.tools import AI_TOOLS_MAP, AI_TOOL_DEFINITIONS
from app.modules.ai.schemas import SmartLeaveResponse

logger = logging.getLogger(__name__)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

async def check_rate_limit_and_log(session: AsyncSession, user_id: str, kind: str, prompt: str, tool_used: Optional[str], response_text: str, latency_ms: int, ok: bool) -> None:
    """Check 20 req/user/hour rate limit and log to ai_logs."""
    try:
        # Check count of requests in past hour using SQL/repo if available, or fallback
        from sqlalchemy import text
        one_hour_ago = datetime.now(timezone.utc).replace(tzinfo=None) # or UTC timestamp
        # Using Taha's core/ai_log helper if available, else direct insert or query
        query = text("SELECT COUNT(*) FROM ai_logs WHERE user_id = :uid AND created_at >= NOW() - INTERVAL '1 hour'")
        res = await session.execute(query, {"uid": user_id})
        count = res.scalar() or 0
        if count >= 20:
            raise HTTPException(status_code=429, detail="AI rate limit exceeded: maximum 20 requests per hour.")

        insert_query = text("""
            INSERT INTO ai_logs (user_id, kind, prompt, tool, response, latency_ms, ok, created_at)
            VALUES (:uid, :kind, :prompt, :tool, :resp, :lat, :ok, NOW())
        """)
        await session.execute(insert_query, {
            "uid": user_id,
            "kind": kind,
            "prompt": prompt[:500], # truncate for safety
            "tool": tool_used,
            "resp": response_text[:1000],
            "lat": latency_ms,
            "ok": ok
        })
        await session.commit()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to log AI request or check rate limit: {e}")
        # Do not block request on log failure if table doesn't exist yet in fresh boot

async def call_groq_chat(session: AsyncSession, user: Any, message: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    """Execute chat with Groq tool calling loop, 15s timeout, policy Q&A, and Roman Urdu support."""
    api_key = os.getenv("AI_API_KEY")
    model = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")
    if not api_key:
        return {"answer": "AI service is not configured (missing API key).", "tool_used": None}

    start_time = datetime.now()
    today_str = datetime.now().strftime("%Y-%m-%d (%A)")

    system_prompt = (
        f"You are the HCM Lite AI Assistant. Today is {today_str}. "
        f"Current user role: {user.role}, employee_id: {user.employee_id}. "
        "Rules: Answer only from tool results or policy guidelines. If you do not know, say 'I don't know'. "
        "Policy guidelines (PROJECT.md §7): Office start 09:00, grace 15 min, half day under 5h, weekend Sat+Sun. "
        "Leave quotas: annual 14, sick 8, casual 10, unpaid unlimited. "
        "Employees cannot view other colleagues' salary or private data. "
        "Roman Urdu support: if the user asks in Roman Urdu (e.g. 'mera leave balance kya hai?'), understand and respond helpfully in Roman Urdu or English while strictly preserving permissions and numbers."
    )

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        for h in history:
            if "role" in h and "content" in h:
                messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    url = f"{GROQ_BASE_URL}/chat/completions"
    tool_used_name = None
    answer = ""

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            # First call to Groq with tools
            resp = await client.post(url, headers=headers, json={
                "model": model,
                "messages": messages,
                "tools": AI_TOOL_DEFINITIONS,
                "tool_choice": "auto"
            })
            if resp.status_code != 200:
                logger.error(f"Groq API error {resp.status_code}: {resp.text}")
                return {"answer": "I'm having trouble connecting to the AI service right now. Please try again.", "tool_used": None}

            data = resp.json()
            choice = data.get("choices", [{}])[0]
            msg = choice.get("message", {})

            tool_calls = msg.get("tool_calls")
            if tool_calls:
                # Handle tool call
                messages.append(msg)
                for tc in tool_calls:
                    fn_name = tc["function"]["name"]
                    fn_args_str = tc["function"]["arguments"]
                    tool_used_name = fn_name
                    try:
                        fn_args = json.loads(fn_args_str) if fn_args_str else {}
                    except json.JSONDecodeError:
                        fn_args = {}

                    tool_fn = AI_TOOLS_MAP.get(fn_name)
                    if tool_fn:
                        tool_result = await tool_fn(session, user, **fn_args)
                    else:
                        tool_result = {"error": f"Unknown tool {fn_name}"}

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "name": fn_name,
                        "content": json.dumps(tool_result)
                    })

                # Second call to Groq after tool results
                resp2 = await client.post(url, headers=headers, json={
                    "model": model,
                    "messages": messages
                })
                if resp2.status_code == 200:
                    data2 = resp2.json()
                    answer = data2.get("choices", [{}])[0].get("message", {}).get("content", "Done.")
                else:
                    answer = "Completed the requested tool action, but failed to format final response."
            else:
                answer = msg.get("content", "Hello! How can I help you with HCM Lite today?")

            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            await check_rate_limit_and_log(session, str(user.id), "chat", message, tool_used_name, answer, elapsed, True)
            return {"answer": answer, "tool_used": tool_used_name}

        except httpx.TimeoutException:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            await check_rate_limit_and_log(session, str(user.id), "chat", message, None, "Timeout", elapsed, False)
            return {"answer": "AI request timed out after 15 seconds. Please try again.", "tool_used": None}
        except Exception as e:
            logger.error(f"Groq chat exception: {e}")
            return {"answer": f"An AI error occurred: {str(e)}", "tool_used": None}

async def call_groq_summarize(session: AsyncSession, user: Any, dashboard: str, from_date: Optional[str], to_date: Optional[str], department_id: Optional[str]) -> List[str]:
    """Generate 3-5 summary bullets from dashboard KPI JSON."""
    if user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Admin or HR role required for summaries.")
    if dashboard == "hr" and user.role == "admin":
        pass # Admin can view HR
    elif dashboard == "admin" and user.role == "hr":
        raise HTTPException(status_code=403, detail="HR cannot view Admin dashboard summaries.")

    # Fetch KPI data from dashboard service
    kpi_data = {}
    try:
        from app.modules.dashboards.service import get_hr_dashboard_service, get_admin_dashboard_service
        if dashboard == "hr":
            kpi_data = await get_hr_dashboard_service(session, user, from_date, to_date, department_id)
        else:
            kpi_data = await get_admin_dashboard_service(session, user, from_date, to_date, department_id)
    except Exception as e:
        kpi_data = {"error": str(e)}

    api_key = os.getenv("AI_API_KEY")
    model = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")
    if not api_key:
        return ["AI key not configured."]

    prompt = f"Here is the {dashboard} dashboard data: {json.dumps(kpi_data)}\nWrite 3 to 5 insightful summary bullets using ONLY these numbers. Do not invent anything."

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(f"{GROQ_BASE_URL}/chat/completions", headers=headers, json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        })
        if resp.status_code != 200:
            return ["Failed to generate summary from AI."]
        text = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        bullets = [b.strip("- *").strip() for b in text.split("\n") if b.strip() and b.strip().startswith(("-", "*", "1", "2", "3", "4", "5"))]
        if not bullets:
            bullets = [text]
        return bullets[:5]

async def call_groq_smart_leave(session: AsyncSession, user: Any, text_input: str) -> Dict[str, Any]:
    """Parse natural language leave request into structured JSON matching SmartLeaveResponse."""
    if user.role not in ["employee", "hr"]:
        raise HTTPException(status_code=403, detail="Employee or HR role required.")

    api_key = os.getenv("AI_API_KEY")
    model = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")
    if not api_key:
        raise HTTPException(status_code=503, detail="AI API key not configured.")

    today_str = datetime.now().strftime("%Y-%m-%d (%A)")

    # Fetch available leave types from DB or service
    leave_types = []
    try:
        from sqlalchemy import text
        res = await session.execute(text("SELECT id, name FROM leave_types"))
        leave_types = [{"id": str(r[0]), "name": r[1]} for r in res.fetchall()]
    except Exception:
        leave_types = [{"id": "annual", "name": "Annual Leave"}, {"id": "sick", "name": "Sick Leave"}, {"id": "casual", "name": "Casual Leave"}]

    prompt = (
        f"Today is {today_str}. Available leave types: {json.dumps(leave_types)}. "
        f"Parse the following employee leave request text into valid JSON with keys: "
        f"leave_type_id (must match one of the IDs above), start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), reason. "
        f"Request: '{text_input}'. Return ONLY raw JSON with no markdown formatting."
    )

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=15.0) as client:
        for attempt in range(2): # Try twice (1 retry)
            try:
                resp = await client.post(f"{GROQ_BASE_URL}/chat/completions", headers=headers, json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1
                })
                if resp.status_code != 200:
                    continue
                content = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                # Clean markdown code blocks if any
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:].strip()

                parsed = json.loads(content)
                # Validate with Pydantic
                validated = SmartLeaveResponse(**parsed)
                return validated.dict()
            except Exception as e:
                logger.warning(f"Smart leave parse attempt {attempt+1} failed: {e}")
                if attempt == 1:
                    raise HTTPException(status_code=422, detail="Could not parse smart leave request. Please use the standard leave form.")
    raise HTTPException(status_code=422, detail="Smart leave parsing failed.")
