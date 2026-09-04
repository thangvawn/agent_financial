from __future__ import annotations

import pytest

from risk_dashboard.modules.financials_product.application.numeric_reviewer import (
    NumericClaim,
    NumericReviewer,
    ReviewDecision,
)
from risk_dashboard.modules.financials_product.schemas.agent_tools import (
    NumericValue,
    ProvenanceRef,
)


def _make_evidence(
    value: float,
    unit: str = "VND_bn",
    period: str = "2024Q3",
    report_id: str = "report:fpt",
    revision_id: str = "rev_valid_123",
) -> NumericValue:
    prov = ProvenanceRef(
        report_id=report_id,
        revision_id=revision_id,
        period=period,
        source="fpt_ir",
        fetched_at="2026-09-01T00:00:00+00:00",
        statement="income_statement",
    )
    return NumericValue(value=value, unit=unit, provenance=prov)  # type: ignore


def test_all_claims_match_passes():
    reviewer = NumericReviewer()
    evidence = [_make_evidence(value=50000.0, unit="VND_bn")]
    claim = NumericClaim(
        claim_id="c1",
        statement="Doanh thu đạt 50,000 tỷ VND",
        value=50000.0,
        unit="VND_bn",
        period="2024Q3",
        report_id="report:fpt",
        revision_id="rev_valid_123",
    )
    decision = reviewer.review([claim], evidence)
    assert decision.verdict == "pass"
    assert "c1" in decision.accepted_claims
    assert len(decision.unsupported_claims) == 0


def test_fabricated_number_rejected():
    reviewer = NumericReviewer()
    evidence = [_make_evidence(value=50000.0, unit="VND_bn")]
    fake_claim = NumericClaim(
        claim_id="c_fake",
        statement="Doanh thu đạt 99,999 tỷ VND",
        value=99999.0,
        unit="VND_bn",
        period="2024Q3",
        report_id="report:fpt",
        revision_id="rev_valid_123",
    )
    decision = reviewer.review([fake_claim], evidence)
    assert decision.verdict == "reject"
    assert "c_fake" in decision.unsupported_claims
    assert len(decision.violations) >= 1


def test_correct_number_wrong_period_rejected():
    reviewer = NumericReviewer()
    evidence = [_make_evidence(value=50000.0, period="2024Q3")]
    claim_wrong_period = NumericClaim(
        claim_id="c_wrong_period",
        statement="Doanh thu Q2 đạt 50,000 tỷ VND",
        value=50000.0,
        unit="VND_bn",
        period="2024Q2",
        report_id="report:fpt",
        revision_id="rev_valid_123",
    )
    decision = reviewer.review([claim_wrong_period], evidence)
    assert decision.verdict == "reject"
    assert "c_wrong_period" in decision.unsupported_claims


def test_unit_swap_rejected():
    reviewer = NumericReviewer()
    evidence = [_make_evidence(value=50000.0, unit="VND_bn")]
    claim_wrong_unit = NumericClaim(
        claim_id="c_unit_swap",
        statement="Doanh thu đạt 50,000 VND",
        value=50000.0,
        unit="VND",
        period="2024Q3",
        report_id="report:fpt",
        revision_id="rev_valid_123",
    )
    decision = reviewer.review([claim_wrong_unit], evidence)
    assert decision.verdict == "reject"
    assert "c_unit_swap" in decision.unsupported_claims


def test_stale_revision_rejected():
    reviewer = NumericReviewer()
    evidence = [_make_evidence(value=50000.0, revision_id="rev_new_456")]
    stale_claim = NumericClaim(
        claim_id="c_stale",
        statement="Doanh thu theo revision cũ là 50,000 tỷ VND",
        value=50000.0,
        unit="VND_bn",
        period="2024Q3",
        report_id="report:fpt",
        revision_id="rev_old_000",
    )
    decision = reviewer.review([stale_claim], evidence)
    assert decision.verdict == "reject"
    assert "c_stale" in decision.unsupported_claims


def test_hypothetical_not_blocked():
    reviewer = NumericReviewer()
    evidence: list[NumericValue] = []
    hypo_claim = NumericClaim(
        claim_id="c_hypo",
        statement="Giả sử doanh thu tăng lên 1,000,000 tỷ VND",
        value=1000000.0,
        unit="VND_bn",
        period="hypothetical",
        report_id="hypothetical",
        revision_id="hypothetical",
        is_hypothetical=True,
    )
    decision = reviewer.review([hypo_claim], evidence)
    assert decision.verdict == "pass"
    assert "c_hypo" in decision.accepted_claims


def test_empty_claims_passes():
    reviewer = NumericReviewer()
    decision = reviewer.review([], [])
    assert decision.verdict == "pass"
    assert len(decision.accepted_claims) == 0
    assert len(decision.unsupported_claims) == 0


def test_mixed_pass_and_reject():
    reviewer = NumericReviewer()
    evidence = [_make_evidence(value=50000.0, unit="VND_bn")]
    c_valid = NumericClaim(
        claim_id="c_valid",
        statement="Doanh thu 50,000 tỷ",
        value=50000.0,
        unit="VND_bn",
        period="2024Q3",
        report_id="report:fpt",
        revision_id="rev_valid_123",
    )
    c_invalid = NumericClaim(
        claim_id="c_invalid",
        statement="Lợi nhuận 20,000 tỷ (bịa)",
        value=20000.0,
        unit="VND_bn",
        period="2024Q3",
        report_id="report:fpt",
        revision_id="rev_valid_123",
    )
    decision = reviewer.review([c_valid, c_invalid], evidence)
    assert decision.verdict == "reject"
    assert "c_valid" in decision.accepted_claims
    assert "c_invalid" in decision.unsupported_claims

