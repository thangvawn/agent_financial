from __future__ import annotations

import pytest
from pydantic import ValidationError

from risk_dashboard.modules.financials_product.domain.numeric_policy import (
    match_numeric_claim_to_evidence,
    validate_numeric_value,
)
from risk_dashboard.modules.financials_product.domain.provenance import (
    calculate_freshness_days,
    derive_revision_id,
    is_fresh,
)
from risk_dashboard.app.registry.registry import get_module_by_slug
from risk_dashboard.modules.financials_product.schemas.agent_tools import (
    BuildEvidenceTableInput,
    BuildEvidenceTableOutput,
    CalculateRatioInput,
    CalculateRatioOutput,
    ComparePeriodsInput,
    ComparePeriodsOutput,
    EvidenceRow,
    NumericValue,
    PeriodDelta,
    ProvenanceRef,
    ResolveLineItemInput,
    ResolveLineItemOutput,
    ResolveReportInput,
    ResolveReportOutput,
    TraceProvenanceInput,
    TraceProvenanceOutput,
    TransformStep,
)
from risk_dashboard.modules.financials_product.schemas.evidence import BCTCEvidenceMemo


def _make_provenance(
    report_id: str = "rep_fpt",
    revision_id: str = "rev_12345678",
    period: str = "2024Q3",
    source: str = "fpt_ir",
    fetched_at: str = "2026-09-01T00:00:00+00:00",
    line_item: str | None = "revenue",
) -> ProvenanceRef:
    return ProvenanceRef(
        report_id=report_id,
        revision_id=revision_id,
        period=period,
        source=source,
        fetched_at=fetched_at,
        statement="income_statement",
        line_item=line_item,
    )


def test_provenance_ref_frozen():
    prov = _make_provenance()
    assert prov.report_id == "rep_fpt"
    with pytest.raises(ValidationError):
        prov.report_id = "changed"  # type: ignore


def test_numeric_value_requires_provenance():
    prov = _make_provenance()
    nv = NumericValue(value=1000.0, unit="VND_bn", scale=1, provenance=prov)
    assert nv.value == 1000.0
    assert nv.provenance.report_id == "rep_fpt"

    with pytest.raises(ValidationError):
        NumericValue(value=1000.0, unit="VND_bn")  # type: ignore


def test_resolve_report_round_trip():
    inp = ResolveReportInput(ticker="FPT", period="2024Q3", refresh=False)
    assert inp.schema_version == "1.0.0"

    out = ResolveReportOutput(
        report_id="rep_fpt",
        revision_id="rev_12345678",
        ticker="FPT",
        company_name="Công ty Cổ phần FPT",
        exchange="HOSE",
        available_periods=("2024Q1", "2024Q2", "2024Q3"),
        active_period="2024Q3",
        source="fpt_ir",
        fetched_at="2026-09-01T00:00:00+00:00",
        freshness_days=1,
        is_private_upload=False,
    )
    dumped = out.model_dump(mode="json")
    loaded = ResolveReportOutput.model_validate(dumped)
    assert loaded == out


def test_resolve_line_item_round_trip():
    prov = _make_provenance(line_item="revenue")
    amount = NumericValue(value=50000.0, unit="VND_bn", scale=1, provenance=prov)
    out = ResolveLineItemOutput(
        line_item="revenue",
        label_vi="Doanh thu thuần",
        amount=amount,
        definition="Doanh thu bán hàng và cung cấp dịch vụ",
        composition=("Doanh thu dịch vụ CNTT", "Doanh thu viễn thông"),
        caveats=("Không bao gồm VAT",),
    )
    dumped = out.model_dump(mode="json")
    loaded = ResolveLineItemOutput.model_validate(dumped)
    assert loaded == out


def test_compare_periods_round_trip():
    prov1 = _make_provenance(period="2023Q3")
    prov2 = _make_provenance(period="2024Q3")
    obs1 = NumericValue(value=40000.0, unit="VND_bn", provenance=prov1)
    obs2 = NumericValue(value=50000.0, unit="VND_bn", provenance=prov2)
    delta_abs = NumericValue(value=10000.0, unit="VND_bn", provenance=prov2)
    delta_pct = NumericValue(value=0.25, unit="pct", provenance=prov2)

    delta = PeriodDelta(
        from_period="2023Q3",
        to_period="2024Q3",
        absolute=delta_abs,
        pct_change=delta_pct,
        formula_id="yoy_growth",
        expression="(to - from) / from",
    )
    out = ComparePeriodsOutput(
        line_item="revenue",
        observations=(obs1, obs2),
        deltas=(delta,),
        limitations=(),
    )
    dumped = out.model_dump(mode="json")
    loaded = ComparePeriodsOutput.model_validate(dumped)
    assert loaded == out


def test_calculate_ratio_round_trip():
    prov = _make_provenance()
    inp_val = NumericValue(value=10000.0, unit="VND_bn", provenance=prov)
    res_val = NumericValue(value=0.20, unit="ratio", provenance=prov)
    out = CalculateRatioOutput(
        formula_id="gross_margin",
        formula_version="1.0.0",
        expression="gross_profit / revenue",
        inputs=(inp_val,),
        result=res_val,
        applicability=("income_statement",),
        limitations=(),
    )
    dumped = out.model_dump(mode="json")
    loaded = CalculateRatioOutput.model_validate(dumped)
    assert loaded == out


def test_trace_provenance_and_evidence_table():
    prov = _make_provenance()
    val = NumericValue(value=123.0, unit="VND_bn", provenance=prov)
    row = EvidenceRow(claim="Doanh thu 123 tỷ", kind="fact", value=val, citation=prov)
    table_out = BuildEvidenceTableOutput(rows=(row,), unsupported_claims=())
    assert len(table_out.rows) == 1

    trace_out = TraceProvenanceOutput(
        claim_ref="claim_1",
        citations=(prov,),
        transformation_chain=(TransformStep(step="fetch", detail="Direct from audited statement"),),
        freshness_days=2,
    )
    assert len(trace_out.citations) == 1


def test_evidence_memo_round_trip():
    prov = _make_provenance()
    val = NumericValue(value=500.0, unit="VND_bn", provenance=prov)
    row = EvidenceRow(claim="Lợi nhuận 500 tỷ", kind="fact", value=val, citation=prov)
    memo = BCTCEvidenceMemo(
        memo_id="memo_001",
        subject="FPT Q3/2024 Evidence Review",
        report_refs=(prov,),
        scope="Review gross margin & revenue growth",
        evidence_rows=(row,),
        calculations=(),
        interpretations=("Doanh nghiệp tăng trưởng ổn định",),
        unresolved_questions=(),
        limitations=("Dựa trên BCTC chưa kiểm toán",),
        reviewer_status="approved",
        is_stale=False,
        expires_at="2026-10-01T00:00:00+00:00",
    )
    dumped = memo.model_dump(mode="json")
    loaded = BCTCEvidenceMemo.model_validate(dumped)
    assert loaded == memo


def test_derive_revision_id_deterministic():
    periods = ("2024Q1", "2024Q2", "2024Q3")
    rev1 = derive_revision_id("fpt_ir", "2026-09-01T00:00:00Z", periods)
    rev2 = derive_revision_id("fpt_ir", "2026-09-01T00:00:00Z", ("2024Q3", "2024Q1", "2024Q2"))
    assert rev1 == rev2
    assert rev1.startswith("rev_")

    rev_diff_time = derive_revision_id("fpt_ir", "2026-09-02T00:00:00Z", periods)
    assert rev1 != rev_diff_time


def test_provenance_freshness_and_numeric_policy():
    days = calculate_freshness_days("2026-08-01T00:00:00+00:00")
    assert days >= 0
    assert is_fresh("2026-09-01T00:00:00+00:00", max_days=90)

    prov = _make_provenance(report_id="rep_1", period="2024Q3")
    val = NumericValue(value=100.0, unit="VND_bn", provenance=prov)
    validate_numeric_value(val)

    matched = match_numeric_claim_to_evidence(
        claim_val=100.0,
        claim_unit="VND_bn",
        claim_period="2024Q3",
        claim_report_id="rep_1",
        evidence_pool=[val],
    )
    assert matched == val

    unmatched = match_numeric_claim_to_evidence(
        claim_val=999.0,
        claim_unit="VND_bn",
        claim_period="2024Q3",
        claim_report_id="rep_1",
        evidence_pool=[val],
    )
    assert unmatched is None


def test_module_permission_scopes():
    mod = get_module_by_slug("financials_product")
    assert mod is not None
    assert "bctc:report:read" in mod.permission_scopes
    assert "bctc:formula:read" in mod.permission_scopes
    assert "bctc:evidence:read" in mod.permission_scopes
