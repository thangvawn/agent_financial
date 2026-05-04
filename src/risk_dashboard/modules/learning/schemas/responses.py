from __future__ import annotations

from pydantic import BaseModel


class LearningHomeResponse(BaseModel):
    path_id: str
    path_label: str
    next_lesson_id: str
    next_lesson_title: str
    recommendation_summary: str
    completed_lessons: int
    completion_pct: int
    feature_flag: str


class LearningGlossaryTermResponse(BaseModel):
    term: str
    definition: str


class LearningQuizQuestionResponse(BaseModel):
    question_id: str
    prompt: str
    options: list[str]


class LearningLessonResponse(BaseModel):
    lesson_id: str
    title: str
    summary: str
    tier: str
    content_type: str
    estimated_minutes: int
    body: list[str]
    glossary: list[LearningGlossaryTermResponse]
    quiz_questions: list[LearningQuizQuestionResponse]
    next_lesson_id: str | None = None
    progress_status: str | None = None
    quiz_score: int | None = None


class LearningQuizSubmitResponse(BaseModel):
    lesson_id: str
    score: int
    passed: bool
    explanations: list[str]
    next_lesson_id: str | None = None


class LearningTutorResponse(BaseModel):
    lesson_id: str
    summary: str
    explanation: str
    check_question: str
    next_lesson_hint: str


class LearningCoachResponse(BaseModel):
    nudge_type: str
    title: str
    message: str
    cta_label: str
    cta_path: str


class LearningContextResponse(BaseModel):
    trigger: str
    recommended_lesson_id: str
    recommended_lesson_title: str
    reason: str


class LearningAssetItemResponse(BaseModel):
    asset_id: str
    kind: str
    file_name: str
    title: str
    url: str
    mime_type: str | None = None
    size_bytes: int
    cover_url: str | None = None


class LearningAssetListResponse(BaseModel):
    kind: str
    items: list[LearningAssetItemResponse]


class LearningCmsStatusResponse(BaseModel):
    enabled: bool
    lesson_count: int
    course_count: int
    path_count: int
    override_count: int
    header_name: str
    legacy_mode: bool = True
    primary_admin_surface: str = "content_ops_admin"
    deprecation_note: str = "Learning CMS hiện chỉ nên dùng cho legacy overrides. Content Ops là đường admin chính."


class LearningCmsGlossaryItemResponse(BaseModel):
    term: str
    definition: str


class LearningCmsQuizQuestionResponse(BaseModel):
    question_id: str
    prompt: str
    options: list[str]
    correct_answer: str
    explanation: str


class LearningCourseAdminResponse(BaseModel):
    course_id: str
    title: str
    description: str
    tier: str
    lesson_ids: list[str]
    doc_status: str
    source: str
    updated_at: str | None = None
    published_at: str | None = None


class LearningPathAdminResponse(BaseModel):
    path_id: str
    title: str
    persona_segment: str
    lesson_ids: list[str]
    description: str
    doc_status: str
    source: str
    updated_at: str | None = None
    published_at: str | None = None


class LearningLessonAdminResponse(BaseModel):
    lesson_id: str
    title: str
    summary: str
    tier: str
    content_type: str
    estimated_minutes: int
    body: list[str]
    glossary: list[LearningCmsGlossaryItemResponse]
    quiz_questions: list[LearningCmsQuizQuestionResponse]
    next_lesson_id: str | None = None
    doc_status: str
    source: str
    updated_at: str | None = None
    published_at: str | None = None
