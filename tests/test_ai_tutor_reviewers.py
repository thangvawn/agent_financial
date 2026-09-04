from __future__ import annotations

from risk_dashboard.modules.ai_tutor.application.reviewers import (
    EvidenceAndNumericReviewer,
    SafetyAndPolicyReviewer,
)
from risk_dashboard.modules.ai_tutor.schemas.conversation import (
    CitationRef,
    NumericClaimRef,
)


def test_evidence_and_numeric_reviewer_accepts_valid_match() -> None:
    reviewer = EvidenceAndNumericReviewer()
    evidence = {"var_95": "0.0245", "cvar_95": "0.0382"}
    citations = (CitationRef(source_type="quant", source_id="quant_engine", label="Quant Risk"),)
    claims = (
        NumericClaimRef(
            claim_id="c1",
            statement="VaR là 0.0245",
            value="0.0245",
            evidence_ref="var_95",
        ),
        NumericClaimRef(
            claim_id="c2",
            statement="CVaR là 0.0382",
            value="0.0382",
            evidence_ref="cvar_95",
        ),
    )

    accepted_cites, accepted_numeric, sanitized_text, rejections = reviewer.review(
        candidate_text="Phân tích VaR và CVaR",
        evidence=evidence,
        citations=citations,
        numeric_claims=claims,
    )

    assert len(rejections) == 0
    assert len(accepted_cites) == 1
    assert len(accepted_numeric) == 2
    assert "Phân tích VaR và CVaR" in sanitized_text


def test_evidence_and_numeric_reviewer_blocks_mismatched_value() -> None:
    reviewer = EvidenceAndNumericReviewer()
    evidence = {"var_95": "0.0245"}
    citations = ()
    claims = (
        NumericClaimRef(
            claim_id="c1",
            statement="VaR là 0.0500 (bịa số)",
            value="0.0500",
            evidence_ref="var_95",
        ),
    )

    _, accepted_numeric, _, rejections = reviewer.review(
        candidate_text="Phân tích",
        evidence=evidence,
        citations=citations,
        numeric_claims=claims,
    )

    assert len(accepted_numeric) == 0
    assert "numeric_mismatch_for_claim_c1" in rejections


def test_safety_and_policy_reviewer() -> None:
    reviewer = SafetyAndPolicyReviewer()
    is_safe, text, rejections, policy_notice = reviewer.review("Anh hãy mua ngay mã này để chắc chắn lãi!")
    assert not is_safe
    assert "contains_investment_advice" in rejections
    assert "không cấu thành khuyến nghị đầu tư" in text
    assert policy_notice is not None

    is_safe_clean, clean_text, clean_rejections, notice = reviewer.review("Chỉ số ROE đo lường hiệu quả sử dụng vốn.")
    assert is_safe_clean
    assert len(clean_rejections) == 0
    assert clean_text == "Chỉ số ROE đo lường hiệu quả sử dụng vốn."
    assert notice is None
