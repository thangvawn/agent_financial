from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class GateEvaluationResult:
    timestamp: str
    single_specialist_score: float
    multi_agent_score: float
    quality_uplift_pp: float
    single_latency_p95_ms: float
    multi_latency_p95_ms: float
    latency_increase_ms: float
    single_cost_usd: float
    multi_cost_usd: float
    cost_increase_pct: float
    decision: str  # "enable_multi_agent" | "keep_single_specialist"
    decision_reason: str


class MultiAgentGateRunner:
    """A/B evaluation gate comparing single specialist against sequential/parallel multi-agent.

    Constraint: Multi-agent mode remains disabled unless quality uplift >= 5.0 pp
    and latency/cost overhead stays within budget.
    """

    def __init__(
        self,
        min_uplift_pp: float = 5.0,
        max_cost_increase_pct: float = 50.0,
        max_latency_p95_ms: float = 8000.0,
    ) -> None:
        self.min_uplift_pp = min_uplift_pp
        self.max_cost_increase_pct = max_cost_increase_pct
        self.max_latency_p95_ms = max_latency_p95_ms
        self._history: list[GateEvaluationResult] = []

    def evaluate(
        self,
        *,
        single_specialist_score: float,
        multi_agent_score: float,
        single_latency_p95_ms: float,
        multi_latency_p95_ms: float,
        single_cost_usd: float,
        multi_cost_usd: float,
    ) -> GateEvaluationResult:
        now_iso = datetime.now(timezone.utc).isoformat()
        uplift_pp = round(multi_agent_score - single_specialist_score, 2)
        latency_inc = round(multi_latency_p95_ms - single_latency_p95_ms, 2)
        cost_inc_pct = (
            round(((multi_cost_usd - single_cost_usd) / single_cost_usd) * 100.0, 2)
            if single_cost_usd > 0
            else 0.0
        )

        # Decision logic
        if uplift_pp < self.min_uplift_pp:
            decision = "keep_single_specialist"
            reason = f"Quality uplift ({uplift_pp} pp) dưới ngưỡng tối thiểu ({self.min_uplift_pp} pp)."
        elif cost_inc_pct > self.max_cost_increase_pct:
            decision = "keep_single_specialist"
            reason = f"Chi phí tăng quá cao ({cost_inc_pct}%) so với ngưỡng ngân sách ({self.max_cost_increase_pct}%)."
        elif multi_latency_p95_ms > self.max_latency_p95_ms:
            decision = "keep_single_specialist"
            reason = f"Độ trễ p95 ({multi_latency_p95_ms}ms) vượt quá giới hạn ({self.max_latency_p95_ms}ms)."
        else:
            decision = "enable_multi_agent"
            reason = f"Đạt chuẩn chất lượng (+{uplift_pp} pp) trong giới hạn chi phí và độ trễ."

        result = GateEvaluationResult(
            timestamp=now_iso,
            single_specialist_score=single_specialist_score,
            multi_agent_score=multi_agent_score,
            quality_uplift_pp=uplift_pp,
            single_latency_p95_ms=single_latency_p95_ms,
            multi_latency_p95_ms=multi_latency_p95_ms,
            latency_increase_ms=latency_inc,
            single_cost_usd=single_cost_usd,
            multi_cost_usd=multi_cost_usd,
            cost_increase_pct=cost_inc_pct,
            decision=decision,
            decision_reason=reason,
        )
        self._history.append(result)
        return result

    def get_history(self) -> list[GateEvaluationResult]:
        return list(self._history)

