from __future__ import annotations

import pytest

from risk_dashboard.modules.learning.evals.gold_set import GOLD_SET_SUITE
from risk_dashboard.modules.learning.evals.multi_agent_runner import LearningMultiAgentEvalRunner
from risk_dashboard.modules.learning.infrastructure.repositories.sqlite import reset_learning_state
from risk_dashboard.platform.database import open_app_state_db
from risk_dashboard.platform.database.migrate import apply_migrations


@pytest.fixture(autouse=True)
def setup_db():
    reset_learning_state()
    with open_app_state_db() as conn:
        apply_migrations(conn)


def test_multi_agent_engine_success_rate() -> None:
    """Verify that Multi-Agent Engine achieves >= 99.5% success rate on 100 gold-set cases."""
    runner = LearningMultiAgentEvalRunner()
    summary = runner.run_suite(GOLD_SET_SUITE)
    assert summary.total_cases >= 100
    success_rate = summary.passed_cases / summary.total_cases
    assert success_rate >= 0.995, f"Success rate {success_rate:.4f} is below 99.5%"
    assert summary.status == "PASSED"


def test_telemetry_records_multi_agent_metrics() -> None:
    """Verify that Multi-Agent Runner records specialized metrics into telemetry collector.

    Expected metrics: total_runs, success_rate, latency_ms_p95, error_types.
    This test is expected to FAIL currently because no dedicated telemetry module exists
    for Multi-Agent Runner (GAP MA-01, GAP MA-02).
    """
    try:
        from risk_dashboard.modules.learning.evals.telemetry import (
            get_multi_agent_telemetry,
            reset_multi_agent_telemetry,
        )
    except ImportError:
        from risk_dashboard.modules.learning.evals.multi_agent_runner import (
            get_multi_agent_telemetry,
            reset_multi_agent_telemetry,
        )

    reset_multi_agent_telemetry()
    runner = LearningMultiAgentEvalRunner()
    runner.run_suite(GOLD_SET_SUITE)

    telemetry = get_multi_agent_telemetry()
    assert telemetry is not None, "Telemetry collector returned None"
    assert "total_runs" in telemetry, "Metric 'total_runs' missing from multi-agent telemetry"
    assert telemetry["total_runs"] >= 100, f"Expected total_runs >= 100, got {telemetry.get('total_runs')}"
    assert "success_rate" in telemetry, "Metric 'success_rate' missing from multi-agent telemetry"
    assert telemetry["success_rate"] >= 0.995, f"Expected success_rate >= 0.995, got {telemetry.get('success_rate')}"
    assert "latency_ms_p95" in telemetry, "Metric 'latency_ms_p95' missing from multi-agent telemetry"
    assert telemetry["latency_ms_p95"] > 0, "Metric 'latency_ms_p95' must be > 0"
    assert "error_types" in telemetry, "Metric 'error_types' missing from multi-agent telemetry"
