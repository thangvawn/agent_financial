from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CreateConversationRequest(BaseModel):
    surface: Literal["learn", "quant", "general", "checkpoint"] = "learn"
    context_id: str | None = None
    idempotency_key: str = Field(min_length=1, max_length=128)


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    surface: Literal["learn", "quant", "general", "checkpoint"] = "learn"
    current_surface_id: str | None = None
    knowledge_level: Literal["beginner", "intermediate", "advanced"] | None = "beginner"
    locale: str = "vi-VN"
    # Optional playback context used to ground answers in the nearby transcript.
    video_time_seconds: float | None = Field(default=None, ge=0, le=86_400)
    idempotency_key: str = Field(min_length=1, max_length=128)


class SubmitFeedbackRequest(BaseModel):
    conversation_id: str | None = None
    rating: Literal["helpful", "not_helpful", "partially_helpful"]
    reason_code: str = "general"
    comment: str | None = Field(default=None, max_length=2000)
    idempotency_key: str = Field(min_length=1, max_length=128)
