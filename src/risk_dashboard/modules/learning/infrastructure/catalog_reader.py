from __future__ import annotations

from typing import Any

from risk_dashboard.modules.admin_cms.infrastructure.repositories.sqlite import SqliteAdminCmsRepository
from risk_dashboard.modules.learning.domain.entities import (
    LearningCourse,
    LearningGlossaryTerm,
    LearningLesson,
    LearningPath,
    LearningQuizQuestion,
)
from risk_dashboard.modules.learning.domain.ports import LearningCatalogReader
from risk_dashboard.modules.learning.infrastructure.catalog import CONTEXT_TRIGGER_TO_LESSON, COURSES, LESSONS, PATHS


def serialize_course(course: LearningCourse) -> dict[str, Any]:
    return {
        "course_id": course.course_id,
        "title": course.title,
        "description": course.description,
        "tier": course.tier,
        "lesson_ids": list(course.lesson_ids),
        "status": course.status,
    }


def deserialize_course(payload: dict[str, Any]) -> LearningCourse:
    return LearningCourse(
        course_id=str(payload["course_id"]),
        title=str(payload["title"]),
        description=str(payload["description"]),
        tier=str(payload["tier"]),
        lesson_ids=[str(item) for item in payload.get("lesson_ids", [])],
        status=str(payload.get("status", "published")),
    )


def serialize_path(path: LearningPath) -> dict[str, Any]:
    return {
        "path_id": path.path_id,
        "title": path.title,
        "persona_segment": path.persona_segment,
        "lesson_ids": list(path.lesson_ids),
        "description": path.description,
        "status": path.status,
    }


def deserialize_path(payload: dict[str, Any]) -> LearningPath:
    return LearningPath(
        path_id=str(payload["path_id"]),
        title=str(payload["title"]),
        persona_segment=str(payload["persona_segment"]),
        lesson_ids=[str(item) for item in payload.get("lesson_ids", [])],
        description=str(payload["description"]),
        status=str(payload.get("status", "published")),
    )


def serialize_lesson(lesson: LearningLesson) -> dict[str, Any]:
    return {
        "lesson_id": lesson.lesson_id,
        "title": lesson.title,
        "summary": lesson.summary,
        "tier": lesson.tier,
        "content_type": lesson.content_type,
        "estimated_minutes": lesson.estimated_minutes,
        "body": list(lesson.body),
        "glossary": [{"term": item.term, "definition": item.definition} for item in lesson.glossary],
        "quiz_questions": [
            {
                "question_id": item.question_id,
                "prompt": item.prompt,
                "options": list(item.options),
                "correct_answer": item.correct_answer,
                "explanation": item.explanation,
            }
            for item in lesson.quiz_questions
        ],
        "next_lesson_id": lesson.next_lesson_id,
        "status": lesson.status,
    }


def deserialize_lesson(payload: dict[str, Any]) -> LearningLesson:
    return LearningLesson(
        lesson_id=str(payload["lesson_id"]),
        title=str(payload["title"]),
        summary=str(payload["summary"]),
        tier=str(payload["tier"]),
        content_type=str(payload["content_type"]),
        estimated_minutes=int(payload["estimated_minutes"]),
        body=[str(item) for item in payload.get("body", [])],
        glossary=[
            LearningGlossaryTerm(term=str(item["term"]), definition=str(item["definition"]))
            for item in payload.get("glossary", [])
        ],
        quiz_questions=[
            LearningQuizQuestion(
                question_id=str(item["question_id"]),
                prompt=str(item["prompt"]),
                options=[str(option) for option in item.get("options", [])],
                correct_answer=str(item["correct_answer"]),
                explanation=str(item["explanation"]),
            )
            for item in payload.get("quiz_questions", [])
        ],
        next_lesson_id=str(payload["next_lesson_id"]) if payload.get("next_lesson_id") else None,
        status=str(payload.get("status", "published")),
    )


class SqliteLearningCatalog(LearningCatalogReader):
    def __init__(
        self,
        content_ops_repo: SqliteAdminCmsRepository | None = None,
    ) -> None:
        self.content_ops_repo = content_ops_repo or SqliteAdminCmsRepository()

    def get_course(self, *, course_id: str) -> LearningCourse:
        return self._resolve_course(course_id)

    def get_path(self, *, path_id: str) -> LearningPath:
        return self._resolve_path(path_id)

    def get_lesson(self, *, lesson_id: str) -> LearningLesson:
        return self._resolve_lesson(lesson_id)

    def get_path_for_persona(self, *, persona_segment: str, primary_route: str) -> LearningPath:
        if primary_route == "financial_health":
            return self.get_path(path_id="financial-health-foundations")
        mapping = {
            "starter": "starter-foundations",
            "household_manager": "financial-health-foundations",
            "beginner_investor": "guided-investing-foundations",
            "advanced_pro": "market-context-fast-track",
            "diaspora_vn": "diaspora-crossborder-foundations",
        }
        return self.get_path(path_id=mapping.get(persona_segment, "starter-foundations"))

    def get_context_lesson_id(self, *, trigger: str) -> str:
        lesson_id = CONTEXT_TRIGGER_TO_LESSON.get(trigger, "money-basics-101")
        self.get_lesson(lesson_id=lesson_id)
        return lesson_id

    def list_courses(self) -> list[LearningCourse]:
        content_ops_published = {
            item.slug: _course_from_content_ops(item=item, payload=version.payload)
            for item, version in self.content_ops_repo.list_published_content(content_type="course")
        }
        ordered_ids = list(dict.fromkeys([*COURSES.keys(), *content_ops_published.keys()]))
        return [
            content_ops_published.get(course_id, COURSES[course_id])
            for course_id in ordered_ids
            if course_id in content_ops_published or course_id in COURSES
        ]

    def list_paths(self) -> list[LearningPath]:
        content_ops_published = {
            item.slug: _path_from_content_ops(item=item, payload=version.payload)
            for item, version in self.content_ops_repo.list_published_content(content_type="path")
        }
        ordered_ids = list(dict.fromkeys([*PATHS.keys(), *content_ops_published.keys()]))
        return [
            content_ops_published.get(path_id, PATHS[path_id])
            for path_id in ordered_ids
            if path_id in content_ops_published or path_id in PATHS
        ]

    def list_lessons(self) -> list[LearningLesson]:
        content_ops_published = {
            item.slug: self._lesson_from_content_ops(item=item, payload=version.payload)
            for item, version in self.content_ops_repo.list_published_content(content_type="lesson")
        }
        ordered_ids = list(dict.fromkeys([*LESSONS.keys(), *content_ops_published.keys()]))
        return [
            content_ops_published.get(lesson_id, LESSONS[lesson_id])
            for lesson_id in ordered_ids
            if lesson_id in content_ops_published or lesson_id in LESSONS
        ]

    def _resolve_course(self, course_id: str) -> LearningCourse:
        content_ops_document = self.content_ops_repo.find_published_content(content_type="course", slug=course_id)
        if content_ops_document is not None:
            item, version = content_ops_document
            return _course_from_content_ops(item=item, payload=version.payload)
        if course_id not in COURSES:
            raise KeyError(course_id)
        return COURSES[course_id]

    def _resolve_path(self, path_id: str) -> LearningPath:
        content_ops_document = self.content_ops_repo.find_published_content(content_type="path", slug=path_id)
        if content_ops_document is not None:
            item, version = content_ops_document
            return _path_from_content_ops(item=item, payload=version.payload)
        if path_id not in PATHS:
            raise KeyError(path_id)
        return PATHS[path_id]

    def _resolve_lesson(self, lesson_id: str) -> LearningLesson:
        content_ops_document = self.content_ops_repo.find_published_content(content_type="lesson", slug=lesson_id)
        if content_ops_document is not None:
            item, version = content_ops_document
            return self._lesson_from_content_ops(item=item, payload=version.payload)
        if lesson_id not in LESSONS:
            raise KeyError(lesson_id)
        return LESSONS[lesson_id]

    def get_context_explainer(self, *, trigger: str) -> dict[str, Any] | None:
        document = self.content_ops_repo.find_published_content(content_type="contextual_explainer", slug=trigger)
        if document is None:
            return None
        item, version = document
        payload = version.payload
        linked_lesson_ids = [str(value) for value in payload.get("linked_lesson_ids", []) if value]
        return {
            "explainer_id": item.slug,
            "title": str(payload.get("title") or item.title),
            "body": _coerce_str_list(payload.get("body") or payload.get("body_json")),
            "linked_lesson_ids": linked_lesson_ids,
            "guardrail_note": str(payload.get("guardrail_note") or ""),
        }

    def _lesson_from_content_ops(self, *, item, payload: dict[str, Any]) -> LearningLesson:
        glossary = _resolve_glossary_terms(
            content_ops_repo=self.content_ops_repo,
            glossary_payload=payload.get("glossary"),
            glossary_refs=payload.get("glossary_refs"),
        )
        return LearningLesson(
            lesson_id=str(payload.get("lesson_id") or item.slug),
            title=str(payload.get("title") or item.title),
            summary=str(payload.get("summary") or payload.get("description") or ""),
            tier=str(payload.get("tier") or "financial_basics"),
            content_type=str(payload.get("content_type") or "micro_lesson"),
            estimated_minutes=int(payload.get("estimated_minutes") or 3),
            body=_coerce_str_list(payload.get("body") or payload.get("body_json")),
            glossary=glossary,
            quiz_questions=_resolve_quiz_questions(payload),
            next_lesson_id=str(payload["next_lesson_id"]) if payload.get("next_lesson_id") else None,
            status="published",
        )


def _course_from_content_ops(*, item, payload: dict[str, Any]) -> LearningCourse:
    return LearningCourse(
        course_id=str(payload.get("course_id") or item.slug),
        title=str(payload.get("title") or item.title),
        description=str(payload.get("description") or payload.get("summary") or ""),
        tier=str(payload.get("tier") or "financial_basics"),
        lesson_ids=[str(value) for value in payload.get("lesson_ids", []) if value],
        status="published",
    )


def _path_from_content_ops(*, item, payload: dict[str, Any]) -> LearningPath:
    return LearningPath(
        path_id=str(payload.get("path_id") or item.slug),
        title=str(payload.get("title") or item.title),
        persona_segment=str(payload.get("persona_segment") or "starter"),
        lesson_ids=[str(value) for value in payload.get("lesson_ids", []) if value],
        description=str(payload.get("description") or payload.get("summary") or ""),
        status="published",
    )


def _coerce_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def _resolve_glossary_terms(
    *,
    content_ops_repo: SqliteAdminCmsRepository,
    glossary_payload: Any,
    glossary_refs: Any,
) -> list[LearningGlossaryTerm]:
    if isinstance(glossary_payload, list) and glossary_payload:
        return [
            LearningGlossaryTerm(
                term=str(item.get("term") or item.get("title") or ""),
                definition=str(item.get("definition") or item.get("short_definition") or item.get("long_definition") or ""),
            )
            for item in glossary_payload
            if isinstance(item, dict) and str(item.get("term") or item.get("title") or "").strip()
        ]
    terms: list[LearningGlossaryTerm] = []
    if not isinstance(glossary_refs, list):
        return terms
    for ref in glossary_refs:
        document = content_ops_repo.find_published_content(content_type="glossary_term", slug=str(ref))
        if document is None:
            continue
        item, version = document
        payload = version.payload
        definition = str(payload.get("short_definition") or payload.get("long_definition") or "")
        terms.append(LearningGlossaryTerm(term=str(payload.get("term") or item.title), definition=definition))
    return terms


def _resolve_quiz_questions(payload: dict[str, Any]) -> list[LearningQuizQuestion]:
    raw_questions = payload.get("quiz_questions") or payload.get("questions_json") or []
    if not isinstance(raw_questions, list):
        return []
    questions: list[LearningQuizQuestion] = []
    for item in raw_questions:
        if not isinstance(item, dict):
            continue
        prompt = str(item.get("prompt") or "").strip()
        if not prompt:
            continue
        questions.append(
            LearningQuizQuestion(
                question_id=str(item.get("question_id") or f"quiz-{len(questions) + 1}"),
                prompt=prompt,
                options=[str(option) for option in item.get("options", []) if str(option).strip()],
                correct_answer=str(item.get("correct_answer") or ""),
                explanation=str(item.get("explanation") or ""),
            )
        )
    return questions
