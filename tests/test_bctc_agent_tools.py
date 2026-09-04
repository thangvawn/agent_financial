from __future__ import annotations

import pytest

from risk_dashboard.modules.financials_product.agent_tools import (
    BctcBuildEvidenceTableTool,
    BctcCalculateRatioTool,
    BctcComparePeriodsTool,
    BctcResolveLineItemTool,
    BctcResolveReportTool,
    BctcTraceProvenanceTool,
    get_bctc_tool_manifests,
)
from risk_dashboard.modules.financials_product.schemas.agent_tools import (
    BuildEvidenceTableInput,
    CalculateRatioInput,
    ComparePeriodsInput,
    ResolveLineItemInput,
    ResolveReportInput,
    TraceProvenanceInput,
)


def test_manifest_registration():
    manifests = get_bctc_tool_manifests()
    assert len(manifests) == 6
    tool_ids = [m.tool_id for m in manifests]
    assert "bctc.resolve_report" in tool_ids
    assert "bctc.resolve_line_item" in tool_ids
    assert "bctc.compare_periods" in tool_ids
    assert "bctc.calculate_ratio" in tool_ids
    assert "bctc.trace_provenance" in tool_ids
    assert "bctc.build_evidence_table" in tool_ids


def test_resolve_report_tool():
    tool = BctcResolveReportTool()
    inp = ResolveReportInput(ticker="FPT")
    out = tool.execute(inp)
    assert out.ticker == "FPT"
    assert out.report_id == "report:fpt"
    assert out.revision_id.startswith("rev_")
    assert len(out.available_periods) > 0
    assert out.active_period in out.available_periods
    assert out.currency == "VND"


def test_resolve_line_item_tool():
    tool = BctcResolveLineItemTool()
    inp = ResolveLineItemInput(
        report_id="report:fpt",
        revision_id="rev_test",
        period="2024Q3",
        line_item="revenue",
    )
    out = tool.execute(inp)
    assert out.line_item == "revenue"
    assert out.amount.provenance is not None
    assert out.amount.provenance.report_id == "report:fpt"
    assert out.amount.provenance.period == "2024Q3"
    assert out.definition != ""


def test_calculate_ratio_valid():
    tool = BctcCalculateRatioTool()
    inp = CalculateRatioInput(
        report_id="report:fpt",
        revision_id="rev_test",
        period="2024Q3",
        formula_id="gross_margin",
    )
    out = tool.execute(inp)
    assert out.formula_id == "gross_margin"
    assert out.result.provenance is not None
    assert out.result.unit == "pct"


def test_calculate_ratio_denominator_zero_or_missing():
    tool = BctcCalculateRatioTool()
    inp = CalculateRatioInput(
        report_id="report:fpt",
        revision_id="rev_test",
        period="9999Q9",  # non-existent period
        formula_id="gross_margin",
    )
    out = tool.execute(inp)
    assert out.result.calculation_status == "insufficient_data"
    assert out.result.value is None


def test_compare_periods_tool():
    tool = BctcComparePeriodsTool()
    # Resolve FPT periods
    rep = BctcResolveReportTool().execute(ResolveReportInput(ticker="FPT"))
    periods = rep.available_periods[-2:] if len(rep.available_periods) >= 2 else ("2023Q4", "2024Q1")
    inp = ComparePeriodsInput(
        report_id="report:fpt",
        revision_id="rev_test",
        line_item="revenue",
        periods=periods,
    )
    out = tool.execute(inp)
    assert out.line_item == "revenue"
    assert len(out.observations) == len(periods)
    assert len(out.deltas) == len(periods) - 1
    for delta in out.deltas:
        assert delta.absolute.provenance is not None
        assert delta.pct_change.provenance is not None


def test_trace_provenance_tool():
    tool = BctcTraceProvenanceTool()
    inp = TraceProvenanceInput(
        report_id="report:fpt",
        revision_id="rev_test",
        claim_ref="claim_rev_1",
    )
    out = tool.execute(inp)
    assert out.claim_ref == "claim_rev_1"
    assert len(out.citations) >= 1
    assert len(out.transformation_chain) >= 1


def test_build_evidence_table_tool():
    tool = BctcBuildEvidenceTableTool()
    inp = BuildEvidenceTableInput(
        report_id="report:fpt",
        revision_id="rev_test",
        claim_refs=("revenue", "gross_profit", "unknown_metric_xyz"),
    )
    out = tool.execute(inp)
    assert len(out.rows) >= 1
    assert "unknown_metric_xyz" in out.unsupported_claims
    for row in out.rows:
        assert row.value.provenance is not None


def test_all_outputs_have_provenance():
    tool_line = BctcResolveLineItemTool()
    out_line = tool_line.execute(ResolveLineItemInput(
        report_id="report:fpt",
        revision_id="rev_test",
        period="2024Q3",
        line_item="revenue",
    ))
    assert out_line.amount.provenance is not None
    assert out_line.amount.provenance.source != ""
    assert out_line.amount.provenance.fetched_at != ""

