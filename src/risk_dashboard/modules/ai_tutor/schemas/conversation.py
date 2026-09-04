from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class CitationRef(BaseModel):
    source_type: Literal["lesson", "quant", "formula", "bctc"] = "lesson"
    source_id: str
    label: str
    url: str | None = None


class NumericClaimRef(BaseModel):
    claim_id: str
    statement: str
    value: str
    unit: str = ""
    evidence_ref: str
    source_version: str = "v1"
    freshness: str = "latest"


class ToolCallRef(BaseModel):
    tool_name: str
    status: Literal["success", "error", "skipped"] = "success"
    summary: str


class MessageEntity(BaseModel):
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
    idempotency_key: str | None = None
    created_at: str


class ConversationEntity(BaseModel):
    conversation_id: str
    account_id: str
    surface: Literal["learn", "quant", "general", "checkpoint"] = "learn"
    context_id: str | None = None
    status: Literal["active", "archived"] = "active"
    title: str | None = None
    idempotency_key: str | None = None
    created_at: str
    updated_at: str


class FeedbackEntity(BaseModel):
    feedback_id: str
    conversation_id: str
    message_id: str
    account_id: str
    rating: Literal["helpful", "not_helpful", "partially_helpful"]
    reason_code: str = "general"
    comment: str | None = None
    idempotency_key: str | None = None
    created_at: str

