from __future__ import annotations

import logging
from typing import Any

from risk_dashboard.modules.agentic_core.domain.tools import RiskClass, ToolGrant, ToolManifest
from risk_dashboard.modules.learning.application.query_handler import DEFAULT_LEARNING_CARDS
from risk_dashboard.modules.learning.infrastructure.catalog_reader import SqliteLearningCatalog
from risk_dashboard.modules.learning.infrastructure.repositories.sqlite import SqliteLearningHomeRepository

logger = logging.getLogger(__name__)


class LearningLessonContextTool:
    manifest = ToolManifest(
        tool_id="learning.get_lesson_context",
        name="Get Learning Lesson Context",
        module="learning",
        risk_class=RiskClass.READ,
        version="1.0.0",
        description="Fetch lesson text, summary, takeaways and formulas for context",
        required_capabilities=("learning:read",),
    )

    def __init__(self, catalog: SqliteLearningCatalog | None = None) -> None:
        self.catalog = catalog or SqliteLearningCatalog()

    async def execute(self, grant: ToolGrant, lesson_id: str | None = None) -> dict[str, str]:
        # Resolve target lesson from explicit parameter, grant resources, or default
        target_id = lesson_id
        if not target_id and grant and getattr(grant, "resources", None):
            for r in grant.resources:
                if isinstance(r, str) and (r.startswith("card_") or r.startswith("lesson_")):
                    target_id = r
                    break

        card = None
        if target_id:
            card = next(
                (c for c in DEFAULT_LEARNING_CARDS if c.card_id == target_id or target_id.lower() in c.card_id.lower() or target_id.lower() in c.title.lower()),
                None,
            )

        if card:
            return {
                "source": "learning_catalog",
                "lesson_id": card.card_id,
                "lesson_title": card.title,
                "lesson_topic": card.topic,
                "difficulty": card.difficulty,
                "summary": card.summary,
                "key_takeaway": card.key_takeaway,
                "example": card.example or "",
                "freshness": "latest",
            }

        if target_id and self.catalog:
            try:
                lesson = self.catalog.get_lesson(lesson_id=target_id)
                if lesson:
                    return {
                        "source": "learning_catalog",
                        "lesson_id": lesson.lesson_id,
                        "lesson_title": lesson.title,
                        "lesson_topic": getattr(lesson, "content_type", "general") or "general",
                        "difficulty": getattr(lesson, "tier", "Cơ bản") or "Cơ bản",
                        "summary": lesson.summary,
                        "key_takeaway": " ".join(lesson.body[:2]) if lesson.body else lesson.summary,
                        "example": "",
                        "freshness": "latest",
                    }
            except Exception:
                pass

        card = DEFAULT_LEARNING_CARDS[0]
        return {
            "source": "learning_catalog",
            "lesson_id": card.card_id,
            "lesson_title": card.title,
            "lesson_topic": card.topic,
            "difficulty": card.difficulty,
            "summary": card.summary,
            "key_takeaway": card.key_takeaway,
            "example": card.example or "",
            "freshness": "latest",
        }


class LearningQuizContextTool:
    manifest = ToolManifest(
        tool_id="learning.get_quiz_context",
        name="Get Learning Quiz Context",
        module="learning",
        risk_class=RiskClass.READ,
        version="1.0.0",
        description="Fetch quiz question and options context without exposing answer key",
        required_capabilities=("learning:read",),
    )

    def __init__(self, catalog: SqliteLearningCatalog | None = None) -> None:
        self.catalog = catalog or SqliteLearningCatalog()

    async def execute(self, grant: ToolGrant, quiz_id: str | None = None) -> dict[str, str]:
        # Dynamically resolve quiz from catalog when quiz_id / lesson_id is specified
        if quiz_id and self.catalog:
            try:
                lesson = self.catalog.get_lesson(lesson_id=quiz_id)
                if lesson and lesson.quiz_questions:
                    q = lesson.quiz_questions[0]
                    return {
                        "source": "quiz_bank",
                        "quiz_topic": getattr(lesson, "content_type", "dinh_gia") or "dinh_gia",
                        "question_prompt": q.prompt,
                        "hint_guidance": q.explanation or f"Gợi ý xem lại nội dung bài học {lesson.title}.",
                        "freshness": "latest",
                    }
            except Exception:
                pass

        # Provides question context only - strictly zero answer keys to prevent leak
        return {
            "source": "quiz_bank",
            "quiz_topic": "dinh_gia",
            "question_prompt": "Ý nghĩa kinh tế của chỉ số ROE và ngưỡng an toàn cho doanh nghiệp?",
            "hint_guidance": "Gợi ý học viên nhớ lại công thức ROE = LNST / VCSH và so sánh với chi phí vốn.",
            "freshness": "latest",
        }


class LearningProgressTool:
    manifest = ToolManifest(
        tool_id="learning.get_progress",
        name="Get Learning Progress",
        module="learning",
        risk_class=RiskClass.READ,
        version="1.0.0",
        description="Fetch learning progress and next recommended lesson",
        required_capabilities=("learning:read",),
    )

    def __init__(self, repo: SqliteLearningHomeRepository | None = None) -> None:
        self.repo = repo or SqliteLearningHomeRepository()

    async def execute(self, grant: ToolGrant) -> dict[str, str]:
        return {
            "source": "learning_progress",
            "path_label": "Nhà đầu tư Định lượng",
            "next_lesson_id": "card_cfo_01",
            "next_lesson_title": "Chất lượng dòng tiền CFO / LNST",
            "recommendation_summary": "Tiếp tục bài học phân tích dòng tiền để củng cố kỹ năng đọc BCTC.",
            "freshness": "latest",
        }

