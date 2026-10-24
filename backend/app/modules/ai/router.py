from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.db import get_db
from app.core.deps import current_user
from app.modules.ai.schemas import ChatRequest, ChatResponse, SummarizeRequest, SummarizeResponse, SmartLeaveRequest, SmartLeaveResponse
from app.modules.ai.service import call_groq_chat, call_groq_summarize, call_groq_smart_leave

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

@router.post("/chat", response_model=dict)
async def ai_chat(payload: ChatRequest, session: AsyncSession = Depends(get_db), user: Any = Depends(current_user)):
    """AI chat assistant with tool calling and policy Q&A."""
    result = await call_groq_chat(session, user, payload.message, payload.history)
    return {"data": result}

@router.post("/summarize", response_model=dict)
async def ai_summarize(payload: SummarizeRequest, session: AsyncSession = Depends(get_db), user: Any = Depends(current_user)):
    """AI dashboard summary for HR or Admin."""
    bullets = await call_groq_summarize(session, user, payload.dashboard, payload.from_date, payload.to_date, payload.department_id)
    return {"data": {"bullets": bullets}}

@router.post("/smart-leave", response_model=dict)
async def ai_smart_leave(payload: SmartLeaveRequest, session: AsyncSession = Depends(get_db), user: Any = Depends(current_user)):
    """Parse natural language leave request into prefilled form fields."""
    result = await call_groq_smart_leave(session, user, payload.text)
    return {"data": result}
