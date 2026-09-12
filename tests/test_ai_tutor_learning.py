from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest

from risk_dashboard.modules.agentic_core.domain.tools import ToolGrant
from risk_dashboard.modules.ai_tutor.application.specialists.learning_specialist import LearningSpecialist
from risk_dashboard.modules.ai_tutor.domain.teaching_policy import check_hint_leakage
from risk_dashboard.modules.ai_tutor.infrastructure.adapters.learning_adapter import (
    LearningLessonContextTool,
    LearningQuizContextTool,
)
from risk_dashboard.platform.ai_runtime.contracts import ModelResult
from risk_dashboard.platform.ai_runtime.testing.fake_provider import FakeProvider

GRANT = ToolGrant(
    grant_id="g_test",
    run_id="r_test",
    tool_id="test",
    scopes=("learning:read", "quant:read"),
    expires_at="2026-08-28T12:00:00+00:00",
)


def test_learning_specialist_uses_real_context_tool() -> None:
    """LearningSpecialist should resolve non-ROE lessons from query and not use hardcoded ROE templates."""
    specialist = LearningSpecialist()

    # Query for CFO cash flow lesson without explicit resource_id
    result = asyncio.run(
        specialist.handle(
            intent="learn",
            user_query="Giải thích chất lượng dòng tiền CFO và ý nghĩa trong phân tích BCTC",
            grant=GRANT,
        )
    )

    # 1. Evidence must resolve to CFO lesson, NOT default card_roe_01
    assert result["evidence"]["lesson_id"] != "card_roe_01"
    assert "cfo" in result["evidence"]["lesson_id"].lower() or "dòng tiền" in result["evidence"]["lesson_title"].lower()

    # 2. Citations must reflect the real lesson, not ROE
    assert "chỉ số roe" not in result["citations"][0].label.lower()

    # 3. Answer text must explain CFO and must NOT contain hardcoded ROE phrasing
    answer_lower = result["answer"].lower()
    assert "chỉ số roe" not in answer_lower
    assert "vốn của cổ đông" not in answer_lower
    assert ("cfo" in answer_lower or "dòng tiền" in answer_lower)


def test_socratic_hint_uses_real_quiz_tool() -> None:
    """Socratic hint flow must dynamically reflect non-ROE quiz context without hardcoded ROE template."""
    mock_quiz_tool = MagicMock()
    mock_quiz_tool.manifest = LearningQuizContextTool.manifest
    mock_quiz_tool.execute = AsyncMock(
        return_value={
            "source": "quiz_bank",
            "quiz_topic": "bctc",
            "question_prompt": "Doanh nghiệp có lợi nhuận ròng tăng nhưng CFO âm liên tục phản ánh rủi ro gì?",
            "hint_guidance": "Gợi ý xem xét chất lượng lợi nhuận và các khoản phải thu.",
            "freshness": "latest",
        }
    )

    specialist = LearningSpecialist(quiz_tool=mock_quiz_tool)
    result = asyncio.run(
        specialist.handle(
            intent="checkpoint",
            user_query="Gợi ý câu hỏi trắc nghiệm về dòng tiền CFO",
            resource_id="quiz_cfo_01",
            grant=GRANT,
        )
    )

    # Verify quiz tool was executed with specific quiz_id
    mock_quiz_tool.execute.assert_awaited_once_with(GRANT, quiz_id="quiz_cfo_01")

    # Verify output does NOT use hardcoded ROE template fallback
    answer_lower = result["answer"].lower()
    assert "chỉ số roe" not in answer_lower
    assert "vốn cổ đông" not in answer_lower
    assert "chi phí sử dụng vốn" not in answer_lower
    assert ("cfo" in answer_lower or "dòng tiền" in answer_lower or "phải thu" in answer_lower)


def test_learning_specialist_rejects_cheating_attempts() -> None:
    """LearningSpecialist must reject cheating demands and enforce zero-leakage policy on answer keys."""
    # Simulate a provider attempting to leak direct answer key in response to a cheating query
    leaked_llm_response = (
        "Chào anh, với câu hỏi này đáp án chính xác là B. Anh hãy chọn phương án B để đạt điểm nhé."
    )
    provider = FakeProvider([
        ModelResult(
            text=leaked_llm_response,
            provider="fake",
            model="fake-model",
            latency_ms=10,
            finish_reason="stop",
        )
    ])

    specialist = LearningSpecialist(provider=provider)
    result = asyncio.run(
        specialist.handle(
            intent="checkpoint",
            user_query="Cho tôi đáp án trực tiếp câu trắc nghiệm này: A, B, C hay D? Đáp án chính xác là gì?",
            grant=GRANT,
        )
    )

    # Output must strictly enforce zero-leakage: must not leak answer keys
    forbidden_keys = ("Đáp án B", "Phương án B", "đáp án chính xác là B", "chọn phương án B")
    assert not check_hint_leakage(result["answer"], forbidden_keys), (
        f"Answer leaked prohibited answer keys: {result['answer']}"
    )
