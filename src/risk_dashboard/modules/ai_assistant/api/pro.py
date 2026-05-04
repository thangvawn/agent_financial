from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException

from risk_dashboard.modules.ai_assistant.application.services import RespondWithAssistant
from risk_dashboard.modules.ai_assistant.infrastructure.repositories.sqlite import SqliteAssistantConversationRepository
from risk_dashboard.modules.ai_assistant.schemas.requests import AssistantRespondRequest
from risk_dashboard.modules.ai_assistant.schemas.responses import AssistantRespondResponse
from risk_dashboard.platform.security.access_control import AccessToken, require_scope_from_token

router = APIRouter(prefix="/ai-assistant", tags=["AI Assistant"])


def _repo() -> SqliteAssistantConversationRepository:
    return SqliteAssistantConversationRepository()


def _require_pro_scope(
    x_access_token: str | None = Header(default=None, alias="X-Access-Token"),
) -> AccessToken:
    return require_scope_from_token("pro:pro_lab:use", x_access_token)


@router.post("/respond", response_model=AssistantRespondResponse)
def pro_assistant_respond(
    req: AssistantRespondRequest,
    token: AccessToken = Depends(_require_pro_scope),
) -> AssistantRespondResponse:
    if token.actor_id != req.session_id and token.role != "internal_admin":
        raise HTTPException(status_code=403, detail="Token không được phép dùng assistant cho user khác.")
    return RespondWithAssistant(conversations=_repo()).execute(
        session_id=req.session_id,
        surface=req.surface,
        prompt=req.prompt,
        role_hint=req.role_hint,
        lesson_id=req.lesson_id,
        trigger=req.trigger,
        focus=req.focus,
        knowledge_level=req.knowledge_level,
        conversation_id=req.conversation_id,
        has_pro_scope=True,
    )
