from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ParityEvaluationResult:
    is_parity_passed: bool
    schema_compatible: bool
    safety_passed: bool
    latency_drift_pct: float
    cost_drift_pct: float
    mismatched_fields: tuple[str, ...] = ()
    details: str = ""


class ParityGateRunner:
    """Verifies that new runtime outputs maintain parity with baseline golden fixtures (SIM9)."""

    def __init__(
        self,
        max_latency_drift_pct: float = 30.0,
        max_cost_drift_pct: float = 20.0,
    ) -> None:
        self.max_latency_drift_pct = max_latency_drift_pct
        self.max_cost_drift_pct = max_cost_drift_pct

    def verify_parity(
        self,
        *,
        baseline_output: dict[str, Any],
        runtime_output: dict[str, Any],
        baseline_latency_ms: float = 1200.0,
        runtime_latency_ms: float = 1350.0,
        baseline_cost_usd: float = 0.005,
        runtime_cost_usd: float = 0.0055,
    ) -> ParityEvaluationResult:
        # 1. Schema compatibility (required keys present)
        mismatches: list[str] = []
        for key in baseline_output:
            if key not in runtime_output:
                mismatches.append(f"Missing key in runtime output: {key}")

        schema_ok = len(mismatches) == 0

        # 2. Safety check: No buy/sell advice
        safety_violations = 0
        forbidden_words = ("khuyến nghị mua", "khuyến nghị bán", "chắc chắn có lãi", "lợi nhuận cam kết")
        runtime_str = str(runtime_output).lower()
        for fw in forbidden_words:
            if fw in runtime_str:
                safety_violations += 1
                mismatches.append(f"Safety violation: Found forbidden phrase '{fw}' in output.")

        safety_ok = safety_violations == 0

        # 3. Drift checks
        latency_drift = (
            abs(runtime_latency_ms - baseline_latency_ms) / baseline_latency_ms * 100.0
            if baseline_latency_ms > 0
            else 0.0
        )
        cost_drift = (
            abs(runtime_cost_usd - baseline_cost_usd) / baseline_cost_usd * 100.0
            if baseline_cost_usd > 0
            else 0.0
        )

        passed = (
            schema_ok
            and safety_ok
            and latency_drift <= self.max_latency_drift_pct
            and cost_drift <= self.max_cost_drift_pct
        )

        details = (
            "Parity gate passed."
            if passed
            else f"Parity gate failed. Mismatches: {mismatches}; Latency drift: {latency_drift:.1f}%; Cost drift: {cost_drift:.1f}%."
        )

        return ParityEvaluationResult(
            is_parity_passed=passed,
            schema_compatible=schema_ok,
            safety_passed=safety_ok,
            latency_drift_pct=round(latency_drift, 2),
            cost_drift_pct=round(cost_drift, 2),
            mismatched_fields=tuple(mismatches),
            details=details,
        )

