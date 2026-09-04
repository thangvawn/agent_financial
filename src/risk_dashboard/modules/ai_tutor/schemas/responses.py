from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

from risk_dashboard.modules.ai_tutor.schemas.conversation import (
    CitationRef,
    NumericClaimRef,
    ToolCallRef,
)


class MessageResponse(BaseModel):
    message_id: str
    conversation_id: str
    role: Literal["user", "assistant"]
    content: str
    intent: str | None = None
    citations: tuple[CitationRef, ...] = ()
    numeric_claims: tuple[NumericClaimRef, ...] = ()
    tool_calls: tuple[ToolCallRef, ...] = ()
    assumptions: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    check_question: str | None = None
    next_action: str | None = None
    trace_id: str | None = None
    created_at: str


class ConversationResponse(BaseModel):
    conversation_id: str
    surface: str
    status: str
    context_id: str | None = None
    title: str | None = None
    created_at: str
    updated_at: str
    message_count: int = Field(ge=0)
    messages: tuple[MessageResponse, ...] = ()


class SendMessageResponse(BaseModel):
    message_id: str
    conversation_id: str
    role: Literal["assistant"] = "assistant"
    answer: str
    citations: tuple[CitationRef, ...] = ()
    numeric_claims: tuple[NumericClaimRef, ...] = ()
    freshness: str = "latest"
    assumptions: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    check_question: str | None = None
    next_action: str | None = None
    trace_id: str | None = None
    tool_calls: tuple[ToolCallRef, ...] = ()
    created_at: str


class FeedbackResponse(BaseModel):
    feedback_id: str
    message_id: str
    status: Literal["recorded"] = "recorded"
    created_at: str

