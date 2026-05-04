from __future__ import annotations

from fastapi import APIRouter

from risk_dashboard.modules.ai_assistant.application.services import RespondWithAssistant, SaveAssistantFeedback
from risk_dashboard.modules.ai_assistant.application.voice import ElevenLabsVoiceRuntime
from risk_dashboard.modules.ai_assistant.infrastructure.repositories.sqlite import SqliteAssistantConversationRepository
from risk_dashboard.modules.ai_assistant.schemas.requests import (
    AssistantFeedbackRequest,
    AssistantRespondRequest,
    AssistantVoiceSynthesizeRequest,
)
from risk_dashboard.modules.ai_assistant.schemas.responses import (
    AssistantFeedbackResponse,
    AssistantRespondResponse,
    AssistantVoiceSynthesizeResponse,
)

router = APIRouter(prefix="/ai-assistant", tags=["AI Assistant"])


def _repo() -> SqliteAssistantConversationRepository:
    return SqliteAssistantConversationRepository()


@router.post("/respond", response_model=AssistantRespondResponse)
def assistant_respond(req: AssistantRespondRequest) -> AssistantRespondResponse:
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
    )


@router.post("/feedback", response_model=AssistantFeedbackResponse)
def assistant_feedback(req: AssistantFeedbackRequest) -> AssistantFeedbackResponse:
    return SaveAssistantFeedback(conversations=_repo()).execute(
        conversation_id=req.conversation_id,
        message_id=req.message_id,
        rating=req.rating,
        reason_code=req.reason_code,
        free_text=req.free_text,
    )


@router.post("/voice/synthesize", response_model=AssistantVoiceSynthesizeResponse)
def assistant_voice_synthesize(req: AssistantVoiceSynthesizeRequest) -> AssistantVoiceSynthesizeResponse:
    result = ElevenLabsVoiceRuntime.from_env().synthesize(
        text=req.text,
        voice_id=req.voice_id,
        model_id=req.model_id,
    )
    return AssistantVoiceSynthesizeResponse(
        provider=result.provider,
        enabled=result.enabled,
        mime_type=result.mime_type,
        audio_base64=result.audio_base64,
        fallback_reason=result.fallback_reason,
        voice_id=result.voice_id,
        model_id=result.model_id,
    )
