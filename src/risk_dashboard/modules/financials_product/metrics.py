"""Prometheus metrics and observability instrumentation for BCTC Agent (Module 5)."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("risk_dashboard.bctc")

try:
    from prometheus_client import Counter, Histogram

    BCTC_TOOL_CALLS_TOTAL = Counter(
        "bctc_tool_calls_total",
        "Total BCTC agent tool invocations",
        ["tool_id", "status"],
    )
    BCTC_UNSUPPORTED_CLAIMS_TOTAL = Counter(
        "bctc_unsupported_claims_total",
        "Total unsupported financial claims blocked by NumericReviewer",
        ["status"],
    )
    BCTC_TOOL_DURATION_SECONDS = Histogram(
        "bctc_tool_duration_seconds",
        "Duration of BCTC tool invocations in seconds",
        ["tool_id", "status"],
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

    BCTC_TOOL_CALLS_TOTAL = _MockMetric()  # type: ignore
    BCTC_UNSUPPORTED_CLAIMS_TOTAL = _MockMetric()  # type: ignore
    BCTC_TOOL_DURATION_SECONDS = _MockMetric()  # type: ignore

