"""Prometheus metrics and observability instrumentation for Simulation Agent (Module 6)."""
from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("risk_dashboard.simulation")

try:
    from prometheus_client import Counter, Histogram

    SIMULATION_TOOL_DURATION_SECONDS = Histogram(
        "simulation_tool_duration_seconds",
        "Duration of simulation tool invocations in seconds",
        ["tool_id", "status"],
    )
    SIMULATION_GROUNDING_FAILURES_TOTAL = Counter(
        "simulation_grounding_failures_total",
        "Total number of simulation grounding gate verification failures",
        ["skill_id"],
    )
    SIMULATION_PROPOSALS_TOTAL = Counter(
        "simulation_proposals_total",
        "Total simulation action proposals created",
        ["status"],
    )
    SIMULATION_EXECUTIONS_TOTAL = Counter(
        "simulation_executions_total",
        "Total simulation action executions",
        ["status"],
    )
except ImportError:
    # Graceful fallback when prometheus_client is not installed
    class _MockMetric:
        def labels(self, *args: Any, **kwargs: Any) -> "_MockMetric":
            return self

        def inc(self, amount: float = 1.0) -> None:
            pass

        def observe(self, amount: float) -> None:
            pass

    SIMULATION_TOOL_DURATION_SECONDS = _MockMetric()  # type: ignore
    SIMULATION_GROUNDING_FAILURES_TOTAL = _MockMetric()  # type: ignore
    SIMULATION_PROPOSALS_TOTAL = _MockMetric()  # type: ignore
    SIMULATION_EXECUTIONS_TOTAL = _MockMetric()  # type: ignore

