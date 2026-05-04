from __future__ import annotations

from pydantic import BaseModel, Field


class OnboardingAnswerItem(BaseModel):
    question_key: str = Field(..., min_length=1, max_length=100)
    answer_value: str = Field(..., min_length=1, max_length=200)


class OnboardingAnswerRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=100)
    answers: list[OnboardingAnswerItem] = Field(default_factory=list, max_length=10)
