from __future__ import annotations

import json
from typing import Any

from risk_dashboard.modules.pro_lab.evals.baseline_fixtures import (
    GOLDEN_BACKTEST_CRITIQUE_OUTPUT,
    GOLDEN_STRATEGY_COPILOT_OUTPUT,
    GOLDEN_SWARM_COMMITTEE_OUTPUT,
)
from risk_dashboard.platform.ai_runtime.contracts import ModelResult, TokenUsage
from risk_dashboard.platform.ai_runtime.testing.fake_provider import FakeProvider


def make_fake_simulation_provider(
    *,
    custom_copilot: dict[str, Any] | None = None,
    custom_critique: dict[str, Any] | None = None,
    custom_swarm: dict[str, Any] | None = None,
) -> FakeProvider:
    """Tạo FakeProvider chứa scripted responses cho cả 3 tác vụ AI của Simulation Agent."""
    copilot_data = custom_copilot or GOLDEN_STRATEGY_COPILOT_OUTPUT
    critique_data = custom_critique or GOLDEN_BACKTEST_CRITIQUE_OUTPUT
    swarm_data = custom_swarm or GOLDEN_SWARM_COMMITTEE_OUTPUT

    by_task = {
        "strategy_copilot": ModelResult(
            text=json.dumps(copilot_data, ensure_ascii=False),
            parsed=copilot_data,
            usage=TokenUsage(prompt=120, completion=180, total=300),
            model_name="fake-gemini-pro",
        ),
        "backtest_critique": ModelResult(
            text=json.dumps(critique_data, ensure_ascii=False),
            parsed=critique_data,
            usage=TokenUsage(prompt=150, completion=200, total=350),
            model_name="fake-gemini-pro",
        ),
        "swarm_committee": ModelResult(
            text=json.dumps(swarm_data, ensure_ascii=False),
            parsed=swarm_data,
            usage=TokenUsage(prompt=200, completion=350, total=550),
            model_name="fake-gemini-pro",
        ),
    }

    return FakeProvider(by_task_type=by_task)

