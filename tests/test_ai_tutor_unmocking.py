from __future__ import annotations

import asyncio
import pytest

from risk_dashboard.modules.agentic_core.domain.tools import ToolGrant
from risk_dashboard.modules.ai_tutor.infrastructure.adapters.learning_adapter import (
    LearningLessonContextTool,
    LearningQuizContextTool,
)
from risk_dashboard.modules.ai_tutor.application.specialists.learning_specialist import LearningSpecialist
from risk_dashboard.modules.ai_tutor.application.specialists.quant_specialist import QuantSpecialist
from risk_dashboard.platform.ai_runtime.contracts import ModelResult
from risk_dashboard.platform.ai_runtime.testing.fake_provider import FakeProvider

GRANT = ToolGrant(
    grant_id="g_test",
    run_id="r_test",
    tool_id="test",
    scopes=("learning:read", "quant:read"),
    expires_at="2026-08-28T12:00:00+00:00",
)


def test_learning_lesson_context_dynamic_resolution():
    tool = LearningLessonContextTool()
    
    # 1. By explicit lesson_id
    res_cfo = asyncio.run(tool.execute(GRANT, lesson_id="card_cfo_01"))
    assert res_cfo["lesson_id"] == "card_cfo_01"
    assert "dòng tiền" in res_cfo["lesson_title"].lower() or "cfo" in res_cfo["lesson_title"].lower()

    # 2. Different lesson_id returns different content
    res_roe = asyncio.run(tool.execute(GRANT, lesson_id="card_roe_01"))
    assert res_roe["lesson_id"] == "card_roe_01"
    assert "roe" in res_roe["lesson_title"].lower()
    assert res_cfo["lesson_title"] != res_roe["lesson_title"]


def test_learning_specialist_invokes_llm_provider():
    custom_llm_text = "Chào anh, đây là câu trả lời được sinh trực tiếp từ mô hình LLM thông qua LLMProvider."
    scripted_res = ModelResult(
        text=custom_llm_text,
        provider="fake",
        model="fake-model",
        latency_ms=15,
        finish_reason="stop",
    )
    provider = FakeProvider([scripted_res])
    specialist = LearningSpecialist(provider=provider)

    result = asyncio.run(
        specialist.handle(
            intent="learn",
            user_query="Giải thích chất lượng dòng tiền CFO",
            resource_id="card_cfo_01",
            grant=GRANT,
        )
    )

    assert result["answer"] == custom_llm_text
    assert len(result["tool_calls"]) > 0
    assert result["evidence"]["lesson_id"] == "card_cfo_01"


def test_quant_specialist_invokes_llm_provider():
    custom_quant_text = "Chào anh, đây là phân tích rủi ro danh mục định lượng được sinh bởi LLM."
    scripted_res = ModelResult(
        text=custom_quant_text,
        provider="fake",
        model="fake-model",
        latency_ms=20,
        finish_reason="stop",
    )
    provider = FakeProvider([scripted_res])
    specialist = QuantSpecialist(provider=provider)

    result = asyncio.run(
        specialist.handle(
            intent="quant",
            user_query="Phân tích chỉ số VaR 95% 1 ngày",
            grant=GRANT,
        )
    )

    assert result["answer"] == custom_quant_text
    assert len(result["numeric_claims"]) >= 2
