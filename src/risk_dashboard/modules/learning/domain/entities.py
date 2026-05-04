from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class LearningQuizQuestion:
    question_id: str
    prompt: str
    options: list[str]
    correct_answer: str
    explanation: str


@dataclass(frozen=True)
class LearningGlossaryTerm:
    term: str
    definition: str


@dataclass(frozen=True)
class LearningLesson:
    lesson_id: str
    title: str
    summary: str
    tier: str
    content_type: str
    estimated_minutes: int
    body: list[str]
    glossary: list[LearningGlossaryTerm]
    quiz_questions: list[LearningQuizQuestion]
    next_lesson_id: str | None = None
    status: str = "published"


@dataclass(frozen=True)
class LearningCourse:
    course_id: str
    title: str
    description: str
    tier: str
    lesson_ids: list[str]
    status: str = "published"


@dataclass(frozen=True)
class LearningPath:
    path_id: str
    title: str
    persona_segment: str
    lesson_ids: list[str]
    description: str
    status: str = "published"


@dataclass(frozen=True)
class LearningProgress:
    user_id: str
    path_id: str
    lesson_id: str
    status: str
    quiz_score: int | None = None
    attempt_count: int = 0
    completed_at: str | None = None
    updated_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class LearningHomeState:
    user_id: str
    path_id: str
    path_label: str
    next_lesson_id: str
    next_lesson_title: str
    recommendation_summary: str
    completed_lessons: int
    completion_pct: int
    updated_at: str


@dataclass(frozen=True)
class LearningTutorReply:
    summary: str
    explanation: str
    check_question: str
    next_lesson_hint: str


@dataclass(frozen=True)
class LearningCoachNudge:
    nudge_type: str
    title: str
    message: str
    cta_label: str
    cta_path: str


@dataclass(frozen=True)
class LearningCmsDocument:
    doc_type: str
    doc_id: str
    status: str
    payload: dict[str, Any]
    updated_at: str
    published_at: str | None = None
