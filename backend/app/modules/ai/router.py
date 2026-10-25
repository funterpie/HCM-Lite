from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, current_user
from app.db import get_session
from app.modules.ai import service
from app.modules.ai.schemas import ChatRequest, SmartLeaveRequest, SummarizeRequest

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat")
async def chat(
    payload: ChatRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(current_user)],
) -> dict:
    return await service.chat(
        session, user, payload.message,
        [turn.model_dump() for turn in payload.history],
    )


@router.post("/summarize")
async def summarize(
    payload: SummarizeRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(current_user)],
) -> dict:
    return await service.summarize(
        session, user, payload.dashboard, payload.from_date,
        payload.to_date, payload.department_id,
    )


@router.post("/smart-leave")
async def smart_leave(
    payload: SmartLeaveRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(current_user)],
) -> dict:
    return await service.smart_leave(session, user, payload.text)
