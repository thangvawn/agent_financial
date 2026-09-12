from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Sequence

from risk_dashboard.modules.learning.agent_tools import (
    LearningGetContextTool,
    LearningGetProgressTool,
    LearningGetQuizItemTool,
    LearningGradeCheckpointTool,
    LearningRecommendNextTool,
    LearningUpdateProgressTool,
)
from risk_dashboard.modules.learning.evals.gold_set import GOLD_SET_SUITE, GoldTestCase
from risk_dashboard.modules.learning.infrastructure.retrieval import sanitize_content
from risk_dashboard.modules.learning.schemas.agent_tools import (
    GetContextInput,
    GetQuizItemInput,
    GradeCheckpointInput,
)


@dataclass(frozen=True)
class EvalRunResult:
    case_id: str
    category: str
    passed: bool
    latency_ms: float
    violations: tuple[str, ...]


@dataclass(frozen=True)
class EvalRunSummary:
    total_cases: int
    passed_cases: int
    grounded_citation_rate: float
    hint_leakage_rate: float
    account_isolation_rate: float
    safety_pass_rate: float
    p50_latency_ms: float
    p95_latency_ms: float
    status: str


class LearningAgentEvalRunner:
    def __init__(self) -> None:
        self.context_tool = LearningGetContextTool()
        self.quiz_tool = LearningGetQuizItemTool()
        self.grade_tool = LearningGradeCheckpointTool()
        self.update_tool = LearningUpdateProgressTool()
        self.progress_tool = LearningGetProgressTool()
        self.recommend_tool = LearningRecommendNextTool()

    def run_case(self, case: GoldTestCase) -> EvalRunResult:
        start = time.perf_counter()
        violations: list[str] = []
        passed = True

        try:
            if case.category == "factual_grounding":
                res = self.context_tool.execute(GetContextInput(lesson_id=case.lesson_id))
                if not res.canonical_content:
                    violations.append("Empty canonical content")
                    passed = False
                if not res.sources or res.sources[0].content_version != "1.0.0":
                    violations.append("Invalid or missing source citation")
                    passed = False

            elif case.category == "formula_numeric":
                res = self.context_tool.execute(GetContextInput(lesson_id=case.lesson_id))
                if not res.canonical_content:
                    violations.append("Missing formula context")
                    passed = False

            elif case.category == "socratic_hint_leakage":
                quiz_res = self.quiz_tool.execute(
                    GetQuizItemInput(lesson_id=case.lesson_id),
                    account_id="eval_user",
                )
                output_str = f"{quiz_res.prompt} {' '.join(quiz_res.options)}".lower()
                for forbidden in case.must_not_contain:
                    if forbidden.lower() in output_str:
                        violations.append(f"Answer leakage detected: '{forbidden}' in output")
                        passed = False

            elif case.category == "misconception_check":
                res = self.context_tool.execute(GetContextInput(lesson_id=case.lesson_id))
                if not res.canonical_content:
                    violations.append("Missing lesson context for misconception check")
                    passed = False

            elif case.category == "prompt_injection_safety":
                sanitized = sanitize_content(case.input_query).lower()
                for forbidden in case.must_not_contain:
                    if forbidden.lower() in sanitized:
                        violations.append(f"Unsafe payload persisted: {forbidden}")
                        passed = False

            elif case.category == "tool_failure_recovery":
                try:
                    self.context_tool.execute(GetContextInput(lesson_id=case.lesson_id))
                    violations.append("Expected tool error for non-existent lesson, but got success")
                    passed = False
                except Exception:
                    passed = True

            elif case.category == "account_isolation":
                cp = self.quiz_tool.execute(GetQuizItemInput(lesson_id=case.lesson_id), account_id="owner_account")
                try:
                    self.grade_tool.execute(
                        GradeCheckpointInput(checkpoint_id=cp.checkpoint_id, response="A"),
                        account_id="attacker_account",
                    )
                    violations.append("Cross-account access was permitted!")
                    passed = False
                except PermissionError:
                    passed = True
                except Exception as exc:
                    violations.append(f"Unexpected exception during isolation check: {exc}")
                    passed = False

        except Exception as exc:
            if case.expected_passed:
                violations.append(f"Unexpected error: {exc}")
                passed = False

        elapsed_ms = (time.perf_counter() - start) * 1000
        return EvalRunResult(
            case_id=case.case_id,
            category=case.category,
            passed=passed,
            latency_ms=elapsed_ms,
            violations=tuple(violations),
        )

    def run_suite(self, suite: Sequence[GoldTestCase] | None = None) -> EvalRunSummary:
        cases_to_run = suite or GOLD_SET_SUITE
        results: list[EvalRunResult] = [self.run_case(c) for c in cases_to_run]

        total = len(results)
        passed_count = sum(1 for r in results if r.passed)
        latencies = sorted(r.latency_ms for r in results)

        p50 = latencies[int(len(latencies) * 0.50)] if latencies else 0.0
        p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0.0

        # Sub-category metrics
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

        return EvalRunSummary(
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


def __getattr__(name: str):
    if name == "LearningMultiAgentEvalRunner":
        from risk_dashboard.modules.learning.evals.multi_agent_runner import (
            LearningMultiAgentEvalRunner,
        )

        return LearningMultiAgentEvalRunner
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


