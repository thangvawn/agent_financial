from __future__ import annotations

from risk_dashboard.modules.analytics_monitoring.application.emitter import emit_product_event
from risk_dashboard.modules.learning.domain.entities import (
    LearningCmsDocument,
    LearningCourse,
    LearningLesson,
    LearningPath,
    LearningProgress,
    utc_now_iso,
)
from risk_dashboard.modules.learning.domain.policies import (
    build_coach_nudge,
    build_initial_learning_home_state,
    build_tutor_reply,
    complete_lesson_progress,
    quiz_progress,
    refresh_learning_home_state,
)
from risk_dashboard.modules.learning.domain.ports import (
    LearningCatalogReader,
    LearningCmsRepository,
    LearningHomeReader,
    LearningHomeWriter,
    LearningProgressRepository,
)
from risk_dashboard.modules.learning.infrastructure.catalog_reader import (
    deserialize_course,
    deserialize_lesson,
    deserialize_path,
    serialize_course,
    serialize_lesson,
    serialize_path,
)
from risk_dashboard.modules.learning.schemas.responses import (
    LearningCoachResponse,
    LearningCmsStatusResponse,
    LearningCourseAdminResponse,
    LearningContextResponse,
    LearningHomeResponse,
    LearningLessonAdminResponse,
    LearningLessonResponse,
    LearningPathAdminResponse,
    LearningQuizSubmitResponse,
    LearningTutorResponse,
)


class GetLearningHome:
    def __init__(self, reader: LearningHomeReader) -> None:
        self.reader = reader

    def execute(self, *, user_id: str) -> LearningHomeResponse:
        state = self.reader.get_home_state(user_id=user_id)
        emit_product_event(
            event_name="learning_home_viewed",
            module="learning",
            surface="learning",
            user_id=user_id,
            session_id=user_id,
            properties={"path_id": state.path_id, "completion_pct": state.completion_pct},
        )
        return LearningHomeResponse(
            path_id=state.path_id,
            path_label=state.path_label,
            next_lesson_id=state.next_lesson_id,
            next_lesson_title=state.next_lesson_title,
            recommendation_summary=state.recommendation_summary,
            completed_lessons=state.completed_lessons,
            completion_pct=state.completion_pct,
            feature_flag="module.learning.enabled",
        )


class SeedLearningHome:
    def __init__(
        self,
        writer: LearningHomeWriter,
        catalog: LearningCatalogReader,
    ) -> None:
        self.writer = writer
        self.catalog = catalog

    def execute(self, *, user_id: str, persona_segment: str, primary_route: str):
        path = self.catalog.get_path_for_persona(persona_segment=persona_segment, primary_route=primary_route)
        first_lesson = self.catalog.get_lesson(lesson_id=path.lesson_ids[0])
        state = build_initial_learning_home_state(user_id=user_id, path=path, first_lesson=first_lesson)
        return self.writer.save_home_state(state)


class GetLearningLesson:
    def __init__(self, catalog: LearningCatalogReader, progress: LearningProgressRepository) -> None:
        self.catalog = catalog
        self.progress = progress

    def execute(self, *, user_id: str, lesson_id: str) -> LearningLessonResponse:
        lesson = self.catalog.get_lesson(lesson_id=lesson_id)
        progress = self.progress.get_progress(user_id=user_id, lesson_id=lesson_id)
        emit_product_event(
            event_name="learning_lesson_opened",
            module="learning",
            surface="learning",
            user_id=user_id,
            session_id=user_id,
            properties={
                "lesson_id": lesson.lesson_id,
                "tier": lesson.tier,
                "content_type": lesson.content_type,
            },
        )
        return _to_lesson_response(lesson, progress)


class SubmitLearningQuiz:
    def __init__(
        self,
        catalog: LearningCatalogReader,
        progress: LearningProgressRepository,
        home_reader: LearningHomeReader,
        home_writer: LearningHomeWriter,
    ) -> None:
        self.catalog = catalog
        self.progress = progress
        self.home_reader = home_reader
        self.home_writer = home_writer

    def execute(self, *, user_id: str, lesson_id: str, answers: dict[str, str]) -> LearningQuizSubmitResponse:
        home = self.home_reader.get_home_state(user_id=user_id)
        lesson = self.catalog.get_lesson(lesson_id=lesson_id)
        previous = self.progress.get_progress(user_id=user_id, lesson_id=lesson_id)
        score, explanations = _grade_quiz(lesson, answers)
        saved = self.progress.save_progress(
            quiz_progress(
                user_id=user_id,
                path_id=home.path_id,
                lesson_id=lesson.lesson_id,
                score=score,
                previous=previous,
            )
        )
        _refresh_home(user_id=user_id, home=home, catalog=self.catalog, progress=self.progress, writer=self.home_writer)
        emit_product_event(
            event_name="learning_quiz_submitted",
            module="learning",
            surface="learning",
            user_id=user_id,
            session_id=user_id,
            properties={"lesson_id": lesson.lesson_id, "quiz_score": score, "passed": saved.status == "completed"},
        )
        if saved.status == "completed":
            emit_product_event(
                event_name="learning_quiz_passed",
                module="learning",
                surface="learning",
                user_id=user_id,
                session_id=user_id,
                properties={"lesson_id": lesson.lesson_id, "quiz_score": score},
            )
        return LearningQuizSubmitResponse(
            lesson_id=lesson.lesson_id,
            score=score,
            passed=saved.status == "completed",
            explanations=explanations,
            next_lesson_id=lesson.next_lesson_id,
        )


class CompleteLearningLesson:
    def __init__(
        self,
        catalog: LearningCatalogReader,
        progress: LearningProgressRepository,
        home_reader: LearningHomeReader,
        home_writer: LearningHomeWriter,
    ) -> None:
        self.catalog = catalog
        self.progress = progress
        self.home_reader = home_reader
        self.home_writer = home_writer

    def execute(self, *, user_id: str, lesson_id: str) -> LearningLessonResponse:
        home = self.home_reader.get_home_state(user_id=user_id)
        lesson = self.catalog.get_lesson(lesson_id=lesson_id)
        previous = self.progress.get_progress(user_id=user_id, lesson_id=lesson_id)
        saved = self.progress.save_progress(
            complete_lesson_progress(
                user_id=user_id,
                path_id=home.path_id,
                lesson_id=lesson.lesson_id,
                previous=previous,
                quiz_score=previous.quiz_score if previous is not None else None,
            )
        )
        _refresh_home(user_id=user_id, home=home, catalog=self.catalog, progress=self.progress, writer=self.home_writer)
        emit_product_event(
            event_name="learning_lesson_completed",
            module="learning",
            surface="learning",
            user_id=user_id,
            session_id=user_id,
            properties={"lesson_id": lesson.lesson_id, "path_id": home.path_id},
        )
        return _to_lesson_response(lesson, saved)


class ExplainLessonWithTutor:
    def __init__(self, catalog: LearningCatalogReader) -> None:
        self.catalog = catalog

    def execute(self, *, lesson_id: str, question: str, knowledge_level: str) -> LearningTutorResponse:
        lesson = self.catalog.get_lesson(lesson_id=lesson_id)
        reply = build_tutor_reply(lesson=lesson, question=question, knowledge_level=knowledge_level)
        emit_product_event(
            event_name="learning_tutor_opened",
            module="learning",
            surface="learning",
            properties={"lesson_id": lesson_id, "knowledge_level": knowledge_level},
        )
        return LearningTutorResponse(
            lesson_id=lesson_id,
            summary=reply.summary,
            explanation=reply.explanation,
            check_question=reply.check_question,
            next_lesson_hint=reply.next_lesson_hint,
        )


class GetLearningCoach:
    def __init__(self, home_reader: LearningHomeReader) -> None:
        self.home_reader = home_reader

    def execute(self, *, user_id: str, trigger: str) -> LearningCoachResponse:
        home = self.home_reader.get_home_state(user_id=user_id)
        nudge = build_coach_nudge(home_state=home, trigger=trigger)
        return LearningCoachResponse(
            nudge_type=nudge.nudge_type,
            title=nudge.title,
            message=nudge.message,
            cta_label=nudge.cta_label,
            cta_path=nudge.cta_path,
        )


class GetContextRecommendation:
    def __init__(self, catalog: LearningCatalogReader) -> None:
        self.catalog = catalog

    def execute(self, *, trigger: str) -> LearningContextResponse:
        explainer = self.catalog.get_context_explainer(trigger=trigger) if hasattr(self.catalog, "get_context_explainer") else None
        lesson_id = self.catalog.get_context_lesson_id(trigger=trigger)
        if explainer is not None and explainer["linked_lesson_ids"]:
            lesson_id = str(explainer["linked_lesson_ids"][0])
        lesson = self.catalog.get_lesson(lesson_id=lesson_id)
        reasons = {
            "drawdown": "Ban dang xem drawdown, nen hoc bai giai thich bien dong truoc khi hanh dong.",
            "compound_interest": "Ban vua hoi ve lai kep, nen di tu compounding basics truoc khi nhay vao ke hoach dai han.",
            "risk_score_low": "Risk score thap la luc nen hoc lai risk basics va xem lai pace cua minh.",
            "goal_off_track": "Goal dang cham tien do nen can bai hoc ve trade-off va pace thuc te.",
            "financial_health_low": "Financial Health yeu nen uu tien bai hoc quy du phong va dong tien truoc.",
        }
        reason = reasons.get(trigger, lesson.summary)
        if explainer is not None:
            body = explainer.get("body") or []
            reason = str(body[0]) if body else reason
        emit_product_event(
            event_name="learning_contextual_explainer_viewed",
            module="learning",
            surface="learning",
            properties={"trigger": trigger, "recommended_lesson_id": lesson.lesson_id},
        )
        return LearningContextResponse(
            trigger=trigger,
            recommended_lesson_id=lesson.lesson_id,
            recommended_lesson_title=lesson.title,
            reason=reason,
        )


class GetLearningCmsStatus:
    def __init__(self, catalog: LearningCatalogReader, cms_repo: LearningCmsRepository) -> None:
        self.catalog = catalog
        self.cms_repo = cms_repo

    def execute(self, *, enabled: bool, header_name: str) -> LearningCmsStatusResponse:
        overrides = sum(
            len(self.cms_repo.list_documents(doc_type=doc_type))
            for doc_type in ("lesson", "course", "path")
        )
        return LearningCmsStatusResponse(
            enabled=enabled,
            lesson_count=len(self.catalog.list_lessons()),
            course_count=len(self.catalog.list_courses()),
            path_count=len(self.catalog.list_paths()),
            override_count=overrides,
            header_name=header_name,
            legacy_mode=True,
            primary_admin_surface="content_ops_admin",
            deprecation_note="Learning CMS hiện chỉ nên dùng cho legacy overrides. Content Ops là đường admin chính cho lesson/course/glossary/explainer/nudge/disclaimer.",
        )


class ListLearningCoursesAdmin:
    def __init__(self, catalog: LearningCatalogReader, cms_repo: LearningCmsRepository) -> None:
        self.catalog = catalog
        self.cms_repo = cms_repo

    def execute(self) -> list[LearningCourseAdminResponse]:
        documents = {doc.doc_id: doc for doc in self.cms_repo.list_documents(doc_type="course")}
        ordered_ids = list(dict.fromkeys([course.course_id for course in self.catalog.list_courses()] + list(documents.keys())))
        return [_course_admin_response(course_id=course_id, catalog=self.catalog, cms_repo=self.cms_repo) for course_id in ordered_ids]


class ListLearningPathsAdmin:
    def __init__(self, catalog: LearningCatalogReader, cms_repo: LearningCmsRepository) -> None:
        self.catalog = catalog
        self.cms_repo = cms_repo

    def execute(self) -> list[LearningPathAdminResponse]:
        documents = {doc.doc_id: doc for doc in self.cms_repo.list_documents(doc_type="path")}
        ordered_ids = list(dict.fromkeys([path.path_id for path in self.catalog.list_paths()] + list(documents.keys())))
        return [_path_admin_response(path_id=path_id, catalog=self.catalog, cms_repo=self.cms_repo) for path_id in ordered_ids]


class ListLearningLessonsAdmin:
    def __init__(self, catalog: LearningCatalogReader, cms_repo: LearningCmsRepository) -> None:
        self.catalog = catalog
        self.cms_repo = cms_repo

    def execute(self) -> list[LearningLessonAdminResponse]:
        documents = {doc.doc_id: doc for doc in self.cms_repo.list_documents(doc_type="lesson")}
        ordered_ids = list(dict.fromkeys([lesson.lesson_id for lesson in self.catalog.list_lessons()] + list(documents.keys())))
        return [_lesson_admin_response(lesson_id=lesson_id, catalog=self.catalog, cms_repo=self.cms_repo) for lesson_id in ordered_ids]


class GetLearningCourseAdmin:
    def __init__(self, catalog: LearningCatalogReader, cms_repo: LearningCmsRepository) -> None:
        self.catalog = catalog
        self.cms_repo = cms_repo

    def execute(self, *, course_id: str) -> LearningCourseAdminResponse:
        return _course_admin_response(course_id=course_id, catalog=self.catalog, cms_repo=self.cms_repo)


class GetLearningPathAdmin:
    def __init__(self, catalog: LearningCatalogReader, cms_repo: LearningCmsRepository) -> None:
        self.catalog = catalog
        self.cms_repo = cms_repo

    def execute(self, *, path_id: str) -> LearningPathAdminResponse:
        return _path_admin_response(path_id=path_id, catalog=self.catalog, cms_repo=self.cms_repo)


class GetLearningLessonAdmin:
    def __init__(self, catalog: LearningCatalogReader, cms_repo: LearningCmsRepository) -> None:
        self.catalog = catalog
        self.cms_repo = cms_repo

    def execute(self, *, lesson_id: str) -> LearningLessonAdminResponse:
        return _lesson_admin_response(lesson_id=lesson_id, catalog=self.catalog, cms_repo=self.cms_repo)


class UpsertLearningCourseAdmin:
    def __init__(self, catalog: LearningCatalogReader, cms_repo: LearningCmsRepository) -> None:
        self.catalog = catalog
        self.cms_repo = cms_repo

    def execute(
        self,
        *,
        course_id: str,
        title: str,
        description: str,
        tier: str,
        lesson_ids: list[str],
        status: str,
    ) -> LearningCourseAdminResponse:
        _validate_referenced_lessons(lesson_ids=lesson_ids, catalog=self.catalog, cms_repo=self.cms_repo)
        course = LearningCourse(
            course_id=course_id,
            title=title,
            description=description,
            tier=tier,
            lesson_ids=lesson_ids,
            status=status,
        )
        now = utc_now_iso()
        self.cms_repo.save_document(
            LearningCmsDocument(
                doc_type="course",
                doc_id=course_id,
                status=status,
                payload=serialize_course(course),
                updated_at=now,
                published_at=now if status == "published" else None,
            )
        )
        return _course_admin_response(course_id=course_id, catalog=self.catalog, cms_repo=self.cms_repo)


class UpsertLearningPathAdmin:
    def __init__(self, catalog: LearningCatalogReader, cms_repo: LearningCmsRepository) -> None:
        self.catalog = catalog
        self.cms_repo = cms_repo

    def execute(
        self,
        *,
        path_id: str,
        title: str,
        persona_segment: str,
        lesson_ids: list[str],
        description: str,
        status: str,
    ) -> LearningPathAdminResponse:
        _validate_referenced_lessons(lesson_ids=lesson_ids, catalog=self.catalog, cms_repo=self.cms_repo)
        path = LearningPath(
            path_id=path_id,
            title=title,
            persona_segment=persona_segment,
            lesson_ids=lesson_ids,
            description=description,
            status=status,
        )
        now = utc_now_iso()
        self.cms_repo.save_document(
            LearningCmsDocument(
                doc_type="path",
                doc_id=path_id,
                status=status,
                payload=serialize_path(path),
                updated_at=now,
                published_at=now if status == "published" else None,
            )
        )
        return _path_admin_response(path_id=path_id, catalog=self.catalog, cms_repo=self.cms_repo)


class UpsertLearningLessonAdmin:
    def __init__(self, catalog: LearningCatalogReader, cms_repo: LearningCmsRepository) -> None:
        self.catalog = catalog
        self.cms_repo = cms_repo

    def execute(
        self,
        *,
        lesson_id: str,
        title: str,
        summary: str,
        tier: str,
        content_type: str,
        estimated_minutes: int,
        body: list[str],
        glossary: list[dict[str, str]],
        quiz_questions: list[dict[str, str | list[str]]],
        next_lesson_id: str | None,
        status: str,
    ) -> LearningLessonAdminResponse:
        if next_lesson_id is not None:
            _validate_referenced_lessons(lesson_ids=[next_lesson_id], catalog=self.catalog, cms_repo=self.cms_repo)
        lesson = deserialize_lesson(
            {
                "lesson_id": lesson_id,
                "title": title,
                "summary": summary,
                "tier": tier,
                "content_type": content_type,
                "estimated_minutes": estimated_minutes,
                "body": body,
                "glossary": glossary,
                "quiz_questions": quiz_questions,
                "next_lesson_id": next_lesson_id,
                "status": status,
            }
        )
        now = utc_now_iso()
        self.cms_repo.save_document(
            LearningCmsDocument(
                doc_type="lesson",
                doc_id=lesson_id,
                status=status,
                payload=serialize_lesson(lesson),
                updated_at=now,
                published_at=now if status == "published" else None,
            )
        )
        return _lesson_admin_response(lesson_id=lesson_id, catalog=self.catalog, cms_repo=self.cms_repo)


def _grade_quiz(lesson: LearningLesson, answers: dict[str, str]) -> tuple[int, list[str]]:
    if not lesson.quiz_questions:
        return 100, []
    correct = 0
    explanations: list[str] = []
    for question in lesson.quiz_questions:
        if answers.get(question.question_id) == question.correct_answer:
            correct += 1
        explanations.append(question.explanation)
    score = round((correct / len(lesson.quiz_questions)) * 100)
    return score, explanations


def _refresh_home(
    *,
    user_id: str,
    home,
    catalog: LearningCatalogReader,
    progress: LearningProgressRepository,
    writer: LearningHomeWriter,
) -> None:
    path = catalog.get_path(path_id=home.path_id)
    lessons = [catalog.get_lesson(lesson_id=lesson_id) for lesson_id in path.lesson_ids]
    progress_items = progress.list_by_path(user_id=user_id, path_id=path.path_id)
    refreshed = refresh_learning_home_state(
        user_id=user_id,
        path=path,
        lessons=lessons,
        progress_items=progress_items,
    )
    writer.save_home_state(refreshed)


def _validate_referenced_lessons(
    *,
    lesson_ids: list[str],
    catalog: LearningCatalogReader,
    cms_repo: LearningCmsRepository,
) -> None:
    for lesson_id in lesson_ids:
        try:
            catalog.get_lesson(lesson_id=lesson_id)
            continue
        except KeyError:
            pass
        document = cms_repo.get_document(doc_type="lesson", doc_id=lesson_id)
        if document is None:
            raise ValueError(f"Unknown lesson reference: {lesson_id}")


def _course_admin_response(
    *,
    course_id: str,
    catalog: LearningCatalogReader,
    cms_repo: LearningCmsRepository,
) -> LearningCourseAdminResponse:
    document = cms_repo.get_document(doc_type="course", doc_id=course_id)
    if document is not None:
        course = deserialize_course(document.payload)
        return LearningCourseAdminResponse(
            course_id=course.course_id,
            title=course.title,
            description=course.description,
            tier=course.tier,
            lesson_ids=course.lesson_ids,
            doc_status=document.status,
            source="cms_override",
            updated_at=document.updated_at,
            published_at=document.published_at,
        )
    course = catalog.get_course(course_id=course_id)
    return LearningCourseAdminResponse(
        course_id=course.course_id,
        title=course.title,
        description=course.description,
        tier=course.tier,
        lesson_ids=course.lesson_ids,
        doc_status=course.status,
        source="base_catalog",
        updated_at=None,
        published_at=None,
    )


def _path_admin_response(
    *,
    path_id: str,
    catalog: LearningCatalogReader,
    cms_repo: LearningCmsRepository,
) -> LearningPathAdminResponse:
    document = cms_repo.get_document(doc_type="path", doc_id=path_id)
    if document is not None:
        path = deserialize_path(document.payload)
        return LearningPathAdminResponse(
            path_id=path.path_id,
            title=path.title,
            persona_segment=path.persona_segment,
            lesson_ids=path.lesson_ids,
            description=path.description,
            doc_status=document.status,
            source="cms_override",
            updated_at=document.updated_at,
            published_at=document.published_at,
        )
    path = catalog.get_path(path_id=path_id)
    return LearningPathAdminResponse(
        path_id=path.path_id,
        title=path.title,
        persona_segment=path.persona_segment,
        lesson_ids=path.lesson_ids,
        description=path.description,
        doc_status=path.status,
        source="base_catalog",
        updated_at=None,
        published_at=None,
    )


def _lesson_admin_response(
    *,
    lesson_id: str,
    catalog: LearningCatalogReader,
    cms_repo: LearningCmsRepository,
) -> LearningLessonAdminResponse:
    document = cms_repo.get_document(doc_type="lesson", doc_id=lesson_id)
    if document is not None:
        lesson = deserialize_lesson(document.payload)
        return LearningLessonAdminResponse(
            lesson_id=lesson.lesson_id,
            title=lesson.title,
            summary=lesson.summary,
            tier=lesson.tier,
            content_type=lesson.content_type,
            estimated_minutes=lesson.estimated_minutes,
            body=lesson.body,
            glossary=[{"term": item.term, "definition": item.definition} for item in lesson.glossary],
            quiz_questions=[
                {
                    "question_id": item.question_id,
                    "prompt": item.prompt,
                    "options": item.options,
                    "correct_answer": item.correct_answer,
                    "explanation": item.explanation,
                }
                for item in lesson.quiz_questions
            ],
            next_lesson_id=lesson.next_lesson_id,
            doc_status=document.status,
            source="cms_override",
            updated_at=document.updated_at,
            published_at=document.published_at,
        )
    lesson = catalog.get_lesson(lesson_id=lesson_id)
    return LearningLessonAdminResponse(
        lesson_id=lesson.lesson_id,
        title=lesson.title,
        summary=lesson.summary,
        tier=lesson.tier,
        content_type=lesson.content_type,
        estimated_minutes=lesson.estimated_minutes,
        body=lesson.body,
        glossary=[{"term": item.term, "definition": item.definition} for item in lesson.glossary],
        quiz_questions=[
            {
                "question_id": item.question_id,
                "prompt": item.prompt,
                "options": item.options,
                "correct_answer": item.correct_answer,
                "explanation": item.explanation,
            }
            for item in lesson.quiz_questions
        ],
        next_lesson_id=lesson.next_lesson_id,
        doc_status=lesson.status,
        source="base_catalog",
        updated_at=None,
        published_at=None,
    )


def _to_lesson_response(lesson: LearningLesson, progress: LearningProgress | None) -> LearningLessonResponse:
    return LearningLessonResponse(
        lesson_id=lesson.lesson_id,
        title=lesson.title,
        summary=lesson.summary,
        tier=lesson.tier,
        content_type=lesson.content_type,
        estimated_minutes=lesson.estimated_minutes,
        body=lesson.body,
        glossary=[{"term": item.term, "definition": item.definition} for item in lesson.glossary],
        quiz_questions=[
            {
                "question_id": item.question_id,
                "prompt": item.prompt,
                "options": item.options,
            }
            for item in lesson.quiz_questions
        ],
        next_lesson_id=lesson.next_lesson_id,
        progress_status=progress.status if progress is not None else None,
        quiz_score=progress.quiz_score if progress is not None else None,
    )
