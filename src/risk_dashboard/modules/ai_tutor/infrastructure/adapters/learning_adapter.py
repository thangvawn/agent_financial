from __future__ import annotations

import logging
from typing import Any

from risk_dashboard.modules.agentic_core.domain.tools import RiskClass, ToolGrant, ToolManifest
from risk_dashboard.modules.learning.application.query_handler import DEFAULT_LEARNING_CARDS, LearningCard
from risk_dashboard.modules.learning.infrastructure.catalog_reader import SqliteLearningCatalog
from risk_dashboard.modules.learning.infrastructure.repositories.sqlite import SqliteLearningHomeRepository

logger = logging.getLogger(__name__)

DEFAULT_CARD_QUIZZES: dict[str, dict[str, str]] = {
    "card_cfo_01": {
        "quiz_topic": "bctc",
        "question_prompt": "Doanh nghiệp có lợi nhuận ròng tăng nhưng CFO âm liên tục phản ánh rủi ro gì?",
        "hint_guidance": "Gợi ý xem xét chất lượng lợi nhuận và các khoản phải thu.",
    },
    "card_risk_01": {
        "quiz_topic": "quan_tri_rui_ro",
        "question_prompt": "Tỷ lệ Nợ vay / Vốn CSH vượt quá 1.5x có thể gây rủi ro gì khi lãi suất tăng?",
        "hint_guidance": "Gợi ý nhớ lại tác động của chi phí lãi vay lên dòng tiền và khả năng chi trả nợ gốc.",
    },
    "card_ta_01": {
        "quiz_topic": "phan_tich_ky_thuat",
        "question_prompt": "Đường SMA 20 cắt lên trên đường SMA 50 (Golden Cross) báo hiệu điều gì về xu hướng giá?",
        "hint_guidance": "Gợi ý xem xét xu hướng giá ngắn hạn và trung hạn.",
    },
    "card_roe_01": {
        "quiz_topic": "dinh_gia",
        "question_prompt": "Ý nghĩa kinh tế của chỉ số ROE và ngưỡng an toàn cho doanh nghiệp?",
        "hint_guidance": "Gợi ý học viên nhớ lại công thức ROE = LNST / VCSH và so sánh với chi phí vốn.",
    },
}


def _format_card_payload(card: LearningCard) -> dict[str, str]:
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

    async def execute(self, grant: ToolGrant, lesson_id: str | None = None, query: str | None = None) -> dict[str, str]:
        target_id = lesson_id
        if not target_id and grant and getattr(grant, "resources", None):
            for r in grant.resources:
                if isinstance(r, str) and (r.startswith("card_") or r.startswith("lesson_")):
                    target_id = r
                    break

        if not target_id and query:
            ql = query.lower()
            if "cfo" in ql or "dòng tiền" in ql:
                target_id = "card_cfo_01"
            elif "nợ" in ql or "đòn bẩy" in ql or "rủi ro" in ql:
                target_id = "card_risk_01"
            elif "sma" in ql or "kỹ thuật" in ql or "xu hướng" in ql:
                target_id = "card_ta_01"
            elif "roe" in ql:
                target_id = "card_roe_01"
            elif self.catalog:
                try:
                    for l in self.catalog.list_lessons():
                        if l.lesson_id.lower() in ql or any(w.lower() in ql for w in l.title.split() if len(w) >= 3):
                            target_id = l.lesson_id
                            break
                except Exception:
                    pass

        if target_id:
            card = next((c for c in DEFAULT_LEARNING_CARDS if c.card_id == target_id or target_id.lower() in c.card_id.lower() or target_id.lower() in c.title.lower()), None)
            if card:
                return _format_card_payload(card)
            if self.catalog:
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

        return _format_card_payload(DEFAULT_LEARNING_CARDS[0])


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

    async def execute(self, grant: ToolGrant, quiz_id: str | None = None, query: str | None = None) -> dict[str, str]:
        target_id = quiz_id
        if not target_id and query:
            ql = query.lower()
            if "cfo" in ql or "dòng tiền" in ql:
                target_id = "card_cfo_01"
            elif "nợ" in ql or "đòn bẩy" in ql:
                target_id = "card_risk_01"
            elif "sma" in ql or "kỹ thuật" in ql:
                target_id = "card_ta_01"
            elif "roe" in ql:
                target_id = "card_roe_01"

        if target_id:
            for k, v in DEFAULT_CARD_QUIZZES.items():
                if k == target_id or target_id.lower() in k.lower():
                    return {"source": "quiz_bank", "quiz_topic": v["quiz_topic"], "question_prompt": v["question_prompt"], "hint_guidance": v["hint_guidance"], "freshness": "latest"}
            if self.catalog:
                try:
                    lesson = self.catalog.get_lesson(lesson_id=target_id)
                    if lesson and lesson.quiz_questions:
                        q = lesson.quiz_questions[0]
                        return {"source": "quiz_bank", "quiz_topic": getattr(lesson, "content_type", "general") or "general", "question_prompt": q.prompt, "hint_guidance": q.explanation or f"Gợi ý xem lại {lesson.title}.", "freshness": "latest"}
                except Exception:
                    pass

        return {"source": "quiz_bank", "quiz_topic": "dinh_gia", "question_prompt": "Ý nghĩa kinh tế của chỉ số ROE và ngưỡng an toàn cho doanh nghiệp?", "hint_guidance": "Gợi ý học viên nhớ lại công thức ROE = LNST / VCSH và so sánh với chi phí vốn.", "freshness": "latest"}


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
