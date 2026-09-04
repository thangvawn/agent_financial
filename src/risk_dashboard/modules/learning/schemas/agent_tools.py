from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class SourceRef(BaseModel):
    source_id: str
    content_version: str
    section_id: str | None = None


class ProgressItem(BaseModel):
    lesson_id: str
    status: str
    quiz_score: int | None = None
    attempt_count: int
    updated_at: str


class GetContextInput(BaseModel):
    schema_version: str = "1.0.0"
    lesson_id: str
    section_id: str | None = None
    locale: str = "vi-VN"


class GetContextOutput(BaseModel):
    schema_version: str = "1.0.0"
    lesson_id: str
    title: str
    canonical_content: tuple[str, ...]
    objectives: tuple[str, ...] = ()
    sources: tuple[SourceRef, ...]
    publication_status: Literal["published"]


class GetProgressInput(BaseModel):
    schema_version: str = "1.0.0"
    path_id: str
    lesson_id: str | None = None


class GetProgressOutput(BaseModel):
    schema_version: str = "1.0.0"
    path_id: str
    items: tuple[ProgressItem, ...]
    completion_pct: int = Field(ge=0, le=100)


class GetQuizItemInput(BaseModel):
    schema_version: str = "1.0.0"
    lesson_id: str
    difficulty: str | None = None


class GetQuizItemOutput(BaseModel):
    schema_version: str = "1.0.0"
    checkpoint_id: str
    lesson_id: str
    prompt: str
    options: tuple[str, ...]
    expires_at: str


class GradeCheckpointInput(BaseModel):
    schema_version: str = "1.0.0"
    checkpoint_id: str
    response: str


class GradeCheckpointOutput(BaseModel):
    schema_version: str = "1.0.0"
    checkpoint_id: str
    lesson_id: str
    passed: bool
    score: int = Field(ge=0, le=100)
    rubric_evidence: tuple[str, ...]
    misconceptions: tuple[str, ...] = ()
    verified_event_id: str


class UpdateProgressInput(BaseModel):
    schema_version: str = "1.0.0"
    verified_event_id: str
    idempotency_key: str
    confirmation_id: str


class UpdateProgressOutput(BaseModel):
    schema_version: str = "1.0.0"
    receipt_id: str
    lesson_id: str
    status: str
    quiz_score: int | None = None
    updated_at: str


class RecommendNextInput(BaseModel):
    schema_version: str = "1.0.0"
    path_id: str
    limit: int = Field(default=3, ge=1, le=10)


class RecommendedItem(BaseModel):
    lesson_id: str
    title: str
    rank: int = Field(ge=1)
    rationale: str


class RecommendNextOutput(BaseModel):
    schema_version: str = "1.0.0"
    path_id: str
    items: tuple[RecommendedItem, ...]

