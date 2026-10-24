from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message to the AI assistant")
    history: Optional[List[Dict[str, str]]] = Field(default=None, description="Chat history list of {role, content}")

class ChatResponse(BaseModel):
    answer: str
    tool_used: Optional[str] = None

class SummarizeRequest(BaseModel):
    dashboard: str = Field(..., description="'hr' or 'admin'")
    from_date: Optional[str] = Field(default=None, alias="from")
    to_date: Optional[str] = Field(default=None, alias="to")
    department_id: Optional[str] = None

class SummarizeResponse(BaseModel):
    bullets: List[str]

class SmartLeaveRequest(BaseModel):
    text: str = Field(..., description="Natural language leave request")

class SmartLeaveResponse(BaseModel):
    leave_type_id: str
    start_date: str
    end_date: str
    reason: str
