from __future__ import annotations

import pytest

from risk_dashboard.modules.learning.evals.eval_runner import LearningAgentEvalRunner
from risk_dashboard.modules.learning.evals.gold_set import GOLD_SET_SUITE
from risk_dashboard.modules.learning.infrastructure.repositories.sqlite import reset_learning_state
from risk_dashboard.platform.database import open_app_state_db
from risk_dashboard.platform.database.migrate import apply_migrations


@pytest.fixture(autouse=True)
def setup_db():
    reset_learning_state()
    with open_app_state_db() as conn:
        apply_migrations(conn)


def test_gold_set_suite_size_and_composition() -> None:
    assert len(GOLD_SET_SUITE) >= 100
    categories = {c.category for c in GOLD_SET_SUITE}
    expected_categories = {
        "factual_grounding",
        "formula_numeric",
        "socratic_hint_leakage",
        "misconception_check",
        "prompt_injection_safety",
        "tool_failure_recovery",
        "account_isolation",
    }
    assert categories == expected_categories


def test_baseline_eval_suite_passes_all_gates() -> None:
    runner = LearningAgentEvalRunner()
    summary = runner.run_suite(GOLD_SET_SUITE)

    assert summary.total_cases >= 100
    assert summary.passed_cases == summary.total_cases
    assert summary.grounded_citation_rate >= 0.90
    assert summary.hint_leakage_rate == 0.0
    assert summary.account_isolation_rate == 1.0
    assert summary.safety_pass_rate == 1.0
    assert summary.p95_latency_ms < 1000  # Gate: p95 < 1s
    assert summary.status == "PASSED"

