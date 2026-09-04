from __future__ import annotations

from risk_dashboard.modules.agentic_core.domain.tools import ToolManifest
from risk_dashboard.modules.financials_product.agent_tools.analysis_tools import (
    CALCULATE_RATIO_MANIFEST,
    COMPARE_PERIODS_MANIFEST,
    BctcCalculateRatioTool,
    BctcComparePeriodsTool,
)
from risk_dashboard.modules.financials_product.agent_tools.evidence_tools import (
    BUILD_EVIDENCE_TABLE_MANIFEST,
    TRACE_PROVENANCE_MANIFEST,
    BctcBuildEvidenceTableTool,
    BctcTraceProvenanceTool,
)
from risk_dashboard.modules.financials_product.agent_tools.report_tools import (
    RESOLVE_LINE_ITEM_MANIFEST,
    RESOLVE_REPORT_MANIFEST,
    BctcResolveLineItemTool,
    BctcResolveReportTool,
)


def get_bctc_tool_manifests() -> list[ToolManifest]:
    return [
        RESOLVE_REPORT_MANIFEST,
        RESOLVE_LINE_ITEM_MANIFEST,
        COMPARE_PERIODS_MANIFEST,
        CALCULATE_RATIO_MANIFEST,
        TRACE_PROVENANCE_MANIFEST,
        BUILD_EVIDENCE_TABLE_MANIFEST,
    ]


__all__ = [
    "RESOLVE_REPORT_MANIFEST",
    "RESOLVE_LINE_ITEM_MANIFEST",
    "COMPARE_PERIODS_MANIFEST",
    "CALCULATE_RATIO_MANIFEST",
    "TRACE_PROVENANCE_MANIFEST",
    "BUILD_EVIDENCE_TABLE_MANIFEST",
    "BctcResolveReportTool",
    "BctcResolveLineItemTool",
    "BctcComparePeriodsTool",
    "BctcCalculateRatioTool",
    "BctcTraceProvenanceTool",
    "BctcBuildEvidenceTableTool",
    "get_bctc_tool_manifests",
]

