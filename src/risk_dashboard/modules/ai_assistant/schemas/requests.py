from __future__ import annotations

from pydantic import BaseModel, Field


class AssistantRespondRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=100)
    surface: str = Field(..., min_length=3, max_length=60)
    prompt: str = Field(default="", max_length=2000)
    role_hint: str | None = Field(default=None, max_length=40)
    lesson_id: str | None = Field(default=None, max_length=120)
    trigger: str | None = Field(default=None, max_length=120)
    focus: str | None = Field(default=None, max_length=120)
    knowledge_level: str | None = Field(default=None, max_length=20)
    conversation_id: str | None = Field(default=None, max_length=80)


class AssistantFeedbackRequest(BaseModel):
    conversation_id: str = Field(..., min_length=6, max_length=80)
    message_id: str = Field(..., min_length=6, max_length=80)
    rating: int = Field(..., ge=1, le=5)
    reason_code: str = Field(..., min_length=2, max_length=80)
    free_text: str | None = Field(default=None, max_length=1000)


class AssistantVoiceSynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=3000)
    session_id: str | None = Field(default=None, min_length=8, max_length=100)
    surface: str | None = Field(default=None, min_length=3, max_length=60)
    role_hint: str | None = Field(default=None, max_length=40)
    voice_id: str | None = Field(default=None, max_length=80)
    model_id: str | None = Field(default=None, max_length=80)
