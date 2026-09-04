from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from risk_dashboard.modules.ai_tutor.application.conversation_service import (
    ConversationNotFoundError,
    ConversationService,
)
from risk_dashboard.modules.ai_tutor.application.feedback_service import (
    FeedbackService,
    MessageNotFoundError,
)
from risk_dashboard.modules.ai_tutor.schemas.requests import (
    CreateConversationRequest,
    SendMessageRequest,
    SubmitFeedbackRequest,
)
from risk_dashboard.modules.ai_tutor.schemas.responses import (
    ConversationResponse,
    FeedbackResponse,
    SendMessageResponse,
)
from risk_dashboard.modules.auth.application.dependencies import resolve_principal
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal

router = APIRouter(prefix="/ai-tutor", tags=["AI Tutor"])


def _conv_service() -> ConversationService:
    return ConversationService()


def _feedback_service() -> FeedbackService:
    return FeedbackService()


@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(
    req: CreateConversationRequest,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> ConversationResponse:
    return _conv_service().create_conversation(
        account_id=principal.account_id, request=req
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: str,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> ConversationResponse:
    try:
        return _conv_service().get_conversation(
            account_id=principal.account_id, conversation_id=conversation_id
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/conversations/{conversation_id}/messages", response_model=SendMessageResponse)
async def send_message(
    conversation_id: str,
    req: SendMessageRequest,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> SendMessageResponse:
    try:
        return await _conv_service().send_message(
            account_id=principal.account_id,
            conversation_id=conversation_id,
            request=req,
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/messages/{message_id}/feedback", response_model=FeedbackResponse)
def submit_feedback(
    message_id: str,
    req: SubmitFeedbackRequest,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> FeedbackResponse:
    try:
        return _feedback_service().submit_feedback(
            account_id=principal.account_id, message_id=message_id, request=req
        )
    except MessageNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

