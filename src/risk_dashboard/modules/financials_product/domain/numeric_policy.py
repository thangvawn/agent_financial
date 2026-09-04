from __future__ import annotations

from typing import Sequence
from risk_dashboard.modules.financials_product.schemas.agent_tools import NumericValue, ProvenanceRef


def validate_numeric_value(numeric_val: NumericValue) -> None:
    """Ensure a numeric value has complete provenance and valid scale."""
    if numeric_val.provenance is None:
        raise ValueError("NumericValue must have non-null provenance.")
    if numeric_val.scale < 1:
        raise ValueError("NumericValue scale must be at least 1.")


def match_numeric_claim_to_evidence(
    claim_val: float,
    claim_unit: str,
    claim_period: str,
    claim_report_id: str,
    evidence_pool: Sequence[NumericValue],
    *,
    tolerance: float = 1e-6,
) -> NumericValue | None:
    """Match a numeric claim against a collection of tool-produced NumericValues."""
    for evidence in evidence_pool:
        if (
            evidence.value is not None
            and abs(evidence.value - claim_val) < tolerance
            and evidence.unit == claim_unit
            and evidence.provenance.period == claim_period
            and evidence.provenance.report_id == claim_report_id
        ):
            return evidence
    return None

