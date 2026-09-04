from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from risk_dashboard.modules.financials_product.schemas.agent_tools import NumericValue


@dataclass(frozen=True)
class NumericClaim:
    claim_id: str
    statement: str
    value: float
    unit: str
    period: str
    report_id: str
    revision_id: str
    is_hypothetical: bool = False


@dataclass(frozen=True)
class ReviewDecision:
    verdict: Literal["pass", "repair", "reject"]
    accepted_claims: tuple[str, ...]
    rejected_claims: tuple[str, ...]
    unsupported_claims: tuple[str, ...] = ()
    violations: tuple[str, ...] = ()


class NumericReviewer:
    """Interceps responses and blocks ungrounded or contradictory numeric statements."""

    def review(
        self,
        claims: Sequence[NumericClaim],
        tool_results: Sequence[NumericValue],
        *,
        tolerance: float = 1e-4,
    ) -> ReviewDecision:
        accepted: list[str] = []
        rejected: list[str] = []
        unsupported: list[str] = []
        violations: list[str] = []

        for claim in claims:
            if claim.is_hypothetical:
                accepted.append(claim.claim_id)
                continue

            matched = self._find_matching_evidence(claim, tool_results, tolerance=tolerance)
            if matched:
                accepted.append(claim.claim_id)
            else:
                unsupported.append(claim.claim_id)
                rejected.append(claim.claim_id)
                violations.append(
                    f"Claim '{claim.claim_id}' (value={claim.value} {claim.unit}, "
                    f"period={claim.period}, rev={claim.revision_id}) has no matching tool evidence."
                )

        verdict: Literal["pass", "repair", "reject"] = "pass" if not unsupported else "reject"

        return ReviewDecision(
            verdict=verdict,
            accepted_claims=tuple(accepted),
            rejected_claims=tuple(rejected),
            unsupported_claims=tuple(unsupported),
            violations=tuple(violations),
        )

    def _find_matching_evidence(
        self,
        claim: NumericClaim,
        results: Sequence[NumericValue],
        *,
        tolerance: float,
    ) -> bool:
        for r in results:
            if r.value is None or r.calculation_status != "ok":
                continue
            if r.unit != claim.unit:
                continue
            if r.provenance.period != claim.period:
                continue
            if r.provenance.report_id != claim.report_id:
                continue
            if r.provenance.revision_id != claim.revision_id:
                continue
            diff = abs(float(r.value) - float(claim.value))
            tol_limit = tolerance * max(1.0, abs(float(claim.value)))
            if diff <= tol_limit or diff < 1e-6:
                return True
        return False

