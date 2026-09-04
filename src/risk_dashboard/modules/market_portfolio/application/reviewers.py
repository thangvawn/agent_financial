from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Literal, Sequence

from risk_dashboard.modules.market_portfolio.domain.agent_policy import check_advisory_safety
from risk_dashboard.modules.market_portfolio.schemas.agent_api import EvidenceRefV1


@dataclass(frozen=True)
class ReviewDecision:
    verdict: Literal["pass", "repair", "reject"]
    violations: tuple[str, ...] = ()
    reason: str = ""


class NumericReviewer:
    """Recomputes deterministic outputs and verifies narrative numeric consistency."""

    def review(
        self,
        narrative: str,
        calculations: dict[str, Any],
        tolerance: float = 0.05,
    ) -> ReviewDecision:
        violations: list[str] = []

        # Find numbers in narrative (e.g. 12.5%, 100,000, 45.2)
        number_strings = re.findall(r"\b\d+(?:[\.,]\d+)?%?\b", narrative)
        clean_nums: list[float] = []
        for s in number_strings:
            clean = s.replace("%", "").replace(",", "")
            try:
                clean_nums.append(float(clean))
            except ValueError:
                continue

        # Extract numeric values from calculations
        calc_nums: list[float] = []
        for val in calculations.values():
            if val is not None:
                try:
                    calc_nums.append(float(str(val).replace("%", "").replace(",", "")))
                except ValueError:
                    continue

        # Check if numbers mentioned in narrative exist in calculations
        unmatched: list[float] = []
        for num in clean_nums:
            if num in (0.0, 1.0, 2.0, 3.0, 100.0):
                continue
            matched = any(abs(num - c) <= tolerance or abs(num - c) / (abs(c) + 1e-9) <= 0.01 for c in calc_nums)
            if not matched:
                unmatched.append(num)

        if len(unmatched) > 0:
            violations.append(f"Narrative contains ungrounded numeric claims: {unmatched[:5]}")

        if violations:
            return ReviewDecision(verdict="repair", violations=tuple(violations), reason="Ungrounded numbers in narrative")
        return ReviewDecision(verdict="pass")


class EvidenceReviewer:
    """Verifies that all evidence references are grounded and complete."""

    def review(self, evidence: Sequence[EvidenceRefV1]) -> ReviewDecision:
        if not evidence:
            return ReviewDecision(
                verdict="reject",
                violations=("No evidence references provided.",),
                reason="Missing evidence references",
            )

        violations: list[str] = []
        for ref in evidence:
            if not ref.tool_call_id or not ref.tool_name or not ref.resource_id:
                violations.append(f"Incomplete EvidenceRefV1: {ref}")
            if ref.output_schema_version != "1.0.0":
                violations.append(f"Unsupported evidence schema version: {ref.output_schema_version}")

        if violations:
            return ReviewDecision(verdict="reject", violations=tuple(violations), reason="Invalid evidence refs")
        return ReviewDecision(verdict="pass")


class SafetyReviewer:
    """Verifies no advisory, buy/sell directives, or missing paper trading disclaimers."""

    def review(self, narrative: str) -> ReviewDecision:
        violations = check_advisory_safety(narrative)
        if violations:
            return ReviewDecision(
                verdict="reject",
                violations=tuple(f"Forbidden advisory phrase detected: {v}" for v in violations),
                reason="Advisory policy violation",
            )

        # Ensure paper context is referenced (strictly requires paper/simulation/educational indicator)
        lower = narrative.lower()
        has_paper = any(term in lower for term in ("paper", "giả lập", "mô phỏng", "học tập", "educational", "sandbox"))
        if not has_paper:
            return ReviewDecision(
                verdict="repair",
                violations=("Missing explicit paper portfolio context indicator.",),
                reason="No paper trading indicator",
            )

        return ReviewDecision(verdict="pass")


