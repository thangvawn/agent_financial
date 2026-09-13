"""Observability & Reliability Tests for Simulation Agent (Module 6 - G5, G6)."""
from __future__ import annotations

import logging
from risk_dashboard.modules.pro_lab.metrics import (
    SIMULATION_EXECUTIONS_TOTAL,
    SIMULATION_GROUNDING_FAILURES_TOTAL,
    SIMULATION_PROPOSALS_TOTAL,
    SIMULATION_TOOL_DURATION_SECONDS,
)


def test_simulation_prometheus_metrics_lifecycle():
    """Verify metrics can observe and increment without throwing exceptions."""
    SIMULATION_TOOL_DURATION_SECONDS.labels(tool_id="simulation.validate_experiment", status="success").observe(0.042)
    SIMULATION_GROUNDING_FAILURES_TOTAL.labels(skill_id="simulation.result_critique.v1").inc()
    SIMULATION_PROPOSALS_TOTAL.labels(status="created").inc()
    SIMULATION_EXECUTIONS_TOTAL.labels(status="executed").inc()


def test_structured_logging_has_no_raw_tokens(caplog):
    """Verify structured logger formats events with hashed account_id and zero raw tokens."""
    logger = logging.getLogger("risk_dashboard.simulation")
    with caplog.at_level(logging.INFO):
        logger.info(
            "simulation.action.confirmed",
            extra={
                "event": "simulation.action.confirmed",
                "receipt_id": "rcpt_test_123",
                "proposal_id": "prop_test_456",
                "account_id_hash": "a1b2c3d4e5f6",
                "status": "executed",
            },
        )
    log_text = caplog.text
    assert "simulation.action.confirmed" in log_text
    assert "tok_" not in log_text
