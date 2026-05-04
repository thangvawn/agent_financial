from __future__ import annotations

from pydantic import BaseModel, Field


class AssistantActionResponse(BaseModel):
    label: str
    path: str
    kind: str = "open_module"


class AssistantSourceResponse(BaseModel):
    label: str
    source_type: str
    freshness: str = "unknown"


class AssistantRespondResponse(BaseModel):
    conversation_id: str
    message_id: str
    role: str
    surface: str
    allowed: bool
    route_decision: str
    title: str
    summary: str
    explanation: str
    next_step: str
    cta_path: str
    confidence_note: str
    guardrails: list[str]
    risk_labels: list[str]
    check_question: str | None = None
    linked_lesson_id: str | None = None
    mode_used: str | None = None
    intent: str | None = None
    intent_confidence: float | None = None
    confidence_label: str | None = None
    data_freshness: str | None = None
    warnings: list[str] = Field(default_factory=list)
    next_actions: list[AssistantActionResponse] = Field(default_factory=list)
    suggested_modules: list[str] = Field(default_factory=list)
    learning_suggestions: list[str] = Field(default_factory=list)
    sources: list[AssistantSourceResponse] = Field(default_factory=list)
    response_blocks: list[dict[str, object]] = Field(default_factory=list)


class AssistantFeedbackResponse(BaseModel):
    saved: bool
    feedback_id: str


class AssistantVoiceSynthesizeResponse(BaseModel):
    provider: str
    enabled: bool
    mime_type: str = "audio/mpeg"
    audio_base64: str | None = None
    fallback_reason: str | None = None
    voice_id: str | None = None
    model_id: str | None = None
