from __future__ import annotations

import asyncio
import pytest

from risk_dashboard.modules.agentic_core.domain.tools import ToolGrant
from risk_dashboard.modules.ai_tutor.infrastructure.adapters.learning_adapter import (
    LearningLessonContextTool,
    LearningProgressTool,
    LearningQuizContextTool,
)
from risk_dashboard.modules.ai_tutor.infrastructure.adapters.quant_adapter import (
    QuantModelReportTool,
    QuantRiskMetricsTool,
    QuantVarSummaryTool,
)

GRANT = ToolGrant(
    grant_id="g1",
    run_id="r1",
    tool_id="test",
    scopes=("learning:read", "quant:read"),
    expires_at="2026-08-28T12:00:00+00:00",
)


def test_learning_lesson_context_tool() -> None:
    tool = LearningLessonContextTool()
    res = asyncio.run(tool.execute(GRANT))
    assert res["source"] == "learning_catalog"
    assert "lesson_title" in res
    assert "summary" in res
    assert "key_takeaway" in res


def test_learning_quiz_context_tool_excludes_answer_key() -> None:
    tool = LearningQuizContextTool()
    res = asyncio.run(tool.execute(GRANT))
    assert res["source"] == "quiz_bank"
    assert "question_prompt" in res
    # Ensure answer keys (A, B, C, D) are not present as correct answer fields
    assert "correct_answer" not in res
    assert "answer_key" not in res


def test_quant_risk_metrics_tool() -> None:
    tool = QuantRiskMetricsTool()
    res = asyncio.run(tool.execute(GRANT))
    assert res["source"] == "quant_engine"
    assert "var_95" in res
    assert "cvar_95" in res
    assert "mc_var_95" in res
    assert float(res["cvar_95"]) >= float(res["var_95"])  # CVaR is always >= VaR
    assert res["confidence"] == "95%"
    assert res["unit"] == "pct"


def test_quant_var_and_model_report_tools() -> None:
    var_tool = QuantVarSummaryTool()
    var_res = asyncio.run(var_tool.execute(GRANT))
    assert var_res["source"] == "var_engine"

    model_tool = QuantModelReportTool()
    model_res = asyncio.run(model_tool.execute(GRANT))
    assert model_res["source"] == "quant_research"
    assert "validation_auc" in model_res
    assert "sharpe_ratio" in model_res

