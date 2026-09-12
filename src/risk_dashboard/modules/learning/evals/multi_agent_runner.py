from __future__ import annotations

from typing import Sequence

from risk_dashboard.modules.learning.evals.eval_runner import (
    EvalRunResult,
    EvalRunSummary,
    LearningAgentEvalRunner,
)
from risk_dashboard.modules.learning.evals.gold_set import GOLD_SET_SUITE, GoldTestCase
from risk_dashboard.modules.learning.evals.telemetry import (
    MultiAgentTelemetryCollector,
    get_multi_agent_collector,
    get_multi_agent_telemetry,
    record_multi_agent_run,
    reset_multi_agent_telemetry,
)


class LearningMultiAgentEvalRunner:
    """E2E Multi-Agent benchmark runner orchestrating the 100 gold test cases with telemetry."""

    def __init__(self, runner: LearningAgentEvalRunner | None = None) -> None:
        self.runner = runner or LearningAgentEvalRunner()

    def run_case(self, case: GoldTestCase) -> EvalRunResult:
        res = self.runner.run_case(case)
        record_multi_agent_run(res)
        return res

    def run_suite(self, suite: Sequence[GoldTestCase] | None = None) -> EvalRunSummary:
        cases_to_run = suite or GOLD_SET_SUITE
        results: list[EvalRunResult] = [self.run_case(c) for c in cases_to_run]

        total = len(results)
        passed_count = sum(1 for r in results if r.passed)
        latencies = sorted(r.latency_ms for r in results)

        p50 = latencies[int(len(latencies) * 0.50)] if latencies else 0.0
        p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0.0

        hint_cases = [r for r in results if r.category == "socratic_hint_leakage"]
        leakage_violations = sum(1 for r in hint_cases if not r.passed)
        hint_leakage_rate = (leakage_violations / len(hint_cases)) if hint_cases else 0.0

        grounding_cases = [r for r in results if r.category in {"factual_grounding", "formula_numeric"}]
        grounding_passed = sum(1 for r in grounding_cases if r.passed)
        grounded_citation_rate = (grounding_passed / len(grounding_cases)) if grounding_cases else 1.0

        isolation_cases = [r for r in results if r.category == "account_isolation"]
        isolation_passed = sum(1 for r in isolation_cases if r.passed)
        account_isolation_rate = (isolation_passed / len(isolation_cases)) if isolation_cases else 1.0

        safety_cases = [r for r in results if r.category == "prompt_injection_safety"]
        safety_passed = sum(1 for r in safety_cases if r.passed)
        safety_pass_rate = (safety_passed / len(safety_cases)) if safety_cases else 1.0

        overall_status = "PASSED" if (passed_count == total and p95 < 1000) else "FAILED"

        summary = EvalRunSummary(
            total_cases=total,
            passed_cases=passed_count,
            grounded_citation_rate=grounded_citation_rate,
            hint_leakage_rate=hint_leakage_rate,
            account_isolation_rate=account_isolation_rate,
            safety_pass_rate=safety_pass_rate,
            p50_latency_ms=p50,
            p95_latency_ms=p95,
            status=overall_status,
        )
        record_multi_agent_run(summary)
        return summary


__all__ = [
    "LearningMultiAgentEvalRunner",
    "MultiAgentTelemetryCollector",
    "get_multi_agent_collector",
    "get_multi_agent_telemetry",
    "record_multi_agent_run",
    "reset_multi_agent_telemetry",
]
