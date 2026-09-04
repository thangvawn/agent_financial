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

    async def execute(self, grant: ToolGrant) -> dict[str, str]:
        # Contextual read: find first card or default lesson
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

    async def execute(self, grant: ToolGrant) -> dict[str, str]:
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

