from __future__ import annotations

from pydantic import BaseModel, Field


class LearningQuizSubmitRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=100)
    answers: dict[str, str]


class LearningTutorRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=100)
    lesson_id: str = Field(..., min_length=3, max_length=100)
    question: str = Field(..., min_length=2, max_length=500)
    knowledge_level: str = Field(default="beginner", min_length=3, max_length=20)


class LearningCoachRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=100)
    trigger: str = Field(default="continue_path", min_length=3, max_length=100)


class LearningCmsGlossaryItemRequest(BaseModel):
    term: str = Field(..., min_length=1, max_length=120)
    definition: str = Field(..., min_length=1, max_length=500)


class LearningCmsQuizQuestionRequest(BaseModel):
    question_id: str = Field(..., min_length=1, max_length=120)
    prompt: str = Field(..., min_length=1, max_length=500)
    options: list[str] = Field(..., min_length=2, max_length=6)
    correct_answer: str = Field(..., min_length=1, max_length=300)
    explanation: str = Field(..., min_length=1, max_length=500)


class LearningCmsLessonUpsertRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    summary: str = Field(..., min_length=3, max_length=400)
    tier: str = Field(..., min_length=3, max_length=60)
    content_type: str = Field(..., min_length=3, max_length=60)
    estimated_minutes: int = Field(..., ge=1, le=60)
    body: list[str] = Field(..., min_length=1, max_length=20)
    glossary: list[LearningCmsGlossaryItemRequest] = Field(default_factory=list, max_length=20)
    quiz_questions: list[LearningCmsQuizQuestionRequest] = Field(default_factory=list, max_length=10)
    next_lesson_id: str | None = Field(default=None, min_length=3, max_length=120)
    status: str = Field(default="draft", pattern="^(draft|published)$")


class LearningCmsCourseUpsertRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=3, max_length=500)
    tier: str = Field(..., min_length=3, max_length=60)
    lesson_ids: list[str] = Field(..., min_length=1, max_length=30)
    status: str = Field(default="draft", pattern="^(draft|published)$")


class LearningCmsPathUpsertRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    persona_segment: str = Field(..., min_length=3, max_length=60)
    lesson_ids: list[str] = Field(..., min_length=1, max_length=30)
    description: str = Field(..., min_length=3, max_length=500)
    status: str = Field(default="draft", pattern="^(draft|published)$")
