import asyncio
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.core.errors import AppError
from app.modules.ai import service as ai_service
from app.modules.ai.schemas import ChatRequest, SmartLeaveRequest, SummarizeRequest
from app.modules.users.schemas import HrUserCreate


def test_ai_request_schemas_validate_inputs():
    request = ChatRequest.model_validate({"message": "Summarize attendance", "history": []})
    assert request.message == "Summarize attendance"
    assert SummarizeRequest.model_validate({"dashboard": "hr"}).dashboard == "hr"
    assert SmartLeaveRequest(text="Need leave next week").text == "Need leave next week"


def test_user_provisioning_rejects_weak_password():
    with pytest.raises(ValidationError):
        HrUserCreate(email="hr@example.com", temp_password="short")


def test_ai_reports_missing_server_key_without_calling_provider(monkeypatch):
    monkeypatch.setattr(ai_service, "get_settings", lambda: SimpleNamespace(ai_api_key=""))
    user = SimpleNamespace(id="123", role="admin")

    with pytest.raises(AppError) as exc_info:
        asyncio.run(ai_service._complete(None, user, "chat", "question", "system"))

    assert exc_info.value.status_code == 503
    assert exc_info.value.code == "ai_not_configured"
