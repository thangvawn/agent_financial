from __future__ import annotations

import inspect
from typing import Any

from risk_dashboard.modules.agentic_core.domain.tools import ToolGrant, ToolManifest
from risk_dashboard.modules.financials_product.agent_tools import (
    BUILD_EVIDENCE_TABLE_MANIFEST,
    CALCULATE_RATIO_MANIFEST,
    COMPARE_PERIODS_MANIFEST,
    RESOLVE_LINE_ITEM_MANIFEST,
    RESOLVE_REPORT_MANIFEST,
    TRACE_PROVENANCE_MANIFEST,
    BctcBuildEvidenceTableTool,
    BctcCalculateRatioTool,
    BctcComparePeriodsTool,
    BctcResolveLineItemTool as CoreBctcResolveLineItemTool,
    BctcResolveReportTool,
    BctcTraceProvenanceTool,
)
from risk_dashboard.modules.financials_product.schemas.agent_tools import (
    BuildEvidenceTableInput,
    CalculateRatioInput,
    ComparePeriodsInput,
    ResolveLineItemInput,
    ResolveReportInput,
    TraceProvenanceInput,
)


def _parse_resource_ticker_and_item(res_id: str | None, default_ticker: str = "FPT", default_item: str = "revenue") -> tuple[str, str]:
    if not res_id:
        return default_ticker, default_item
    parts = res_id.split(":")
    if len(parts) >= 3 and parts[0] == "ticker":
        return parts[1], parts[2]
    if len(parts) == 2:
        return parts[0], parts[1]
    if len(parts) == 1 and parts[0]:
        return parts[0], default_item
    return default_ticker, default_item


class BctcResolveReportDomainTool:
    manifest = RESOLVE_REPORT_MANIFEST

    def __init__(self, manifest: ToolManifest | None = None, service: Any = None) -> None:
        self.manifest = manifest or RESOLVE_REPORT_MANIFEST
        self.service = service
        self._underlying = BctcResolveReportTool()

    async def execute(self, grant: ToolGrant) -> dict[str, str]:
        ticker, _ = _parse_resource_ticker_and_item(getattr(grant, "resource_id", None))
        res = self._underlying.execute(ResolveReportInput(ticker=ticker))
        return {
            "tool_id": self.manifest.tool_id,
            "status": "resolved",
            "report_id": res.report_id,
            "revision_id": res.revision_id,
            "ticker": res.ticker,
            "active_period": res.active_period,
            "available_periods": ",".join(res.available_periods),
            "source": res.source,
        }


class BctcResolveLineItemDomainTool:
    manifest = RESOLVE_LINE_ITEM_MANIFEST

    def __init__(self, manifest: ToolManifest | None = None, service: Any = None) -> None:
        self.manifest = manifest or RESOLVE_LINE_ITEM_MANIFEST
        self.service = service
        self._underlying = CoreBctcResolveLineItemTool()

    async def execute(self, grant: ToolGrant) -> dict[str, str]:
        ticker, line_item = _parse_resource_ticker_and_item(getattr(grant, "resource_id", None))
        if self.service is not None:
            if inspect.iscoroutinefunction(self.service):
                out = await self.service(ticker, line_item)
            else:
                out = self.service(ticker, line_item)
            if isinstance(out, dict):
                return {str(k): str(v) for k, v in out.items()}

        res = self._underlying.execute(
            ResolveLineItemInput(
                report_id=f"report:{ticker.lower()}",
                revision_id="",
                period="",
                line_item=line_item,
            )
        )
        return {
            "tool_id": self.manifest.tool_id,
            "status": "resolved",
            "ticker": ticker,
            "line_item": line_item,
            "value": str(res.amount.value) if res.amount.value is not None else "0",
            "unit": res.amount.unit,
            "currency": "VND",
            "period": res.amount.provenance.period if res.amount.provenance else "",
            "revision_id": res.amount.provenance.revision_id if res.amount.provenance else "",
            "definition": res.definition,
        }


class BctcComparePeriodsDomainTool:
    manifest = COMPARE_PERIODS_MANIFEST

    def __init__(self, manifest: ToolManifest | None = None, service: Any = None) -> None:
        self.manifest = manifest or COMPARE_PERIODS_MANIFEST
        self.service = service
        self._underlying = BctcComparePeriodsTool()

    async def execute(self, grant: ToolGrant) -> dict[str, str]:
        ticker, line_item = _parse_resource_ticker_and_item(getattr(grant, "resource_id", None))
        res = self._underlying.execute(
            ComparePeriodsInput(
                report_id=f"report:{ticker.lower()}",
                revision_id="",
                line_item=line_item,
                periods=("2023Q4", "2024Q1"),
            )
        )
        return {
            "tool_id": self.manifest.tool_id,
            "status": "resolved",
            "line_item": res.line_item,
            "deltas_count": str(len(res.deltas)),
        }


class BctcCalculateRatioDomainTool:
    manifest = CALCULATE_RATIO_MANIFEST

    def __init__(self, manifest: ToolManifest | None = None, service: Any = None) -> None:
        self.manifest = manifest or CALCULATE_RATIO_MANIFEST
        self.service = service
        self._underlying = BctcCalculateRatioTool()

    async def execute(self, grant: ToolGrant) -> dict[str, str]:
        ticker, formula_id = _parse_resource_ticker_and_item(
            getattr(grant, "resource_id", None), default_item="gross_margin"
        )
        res = self._underlying.execute(
            CalculateRatioInput(
                report_id=f"report:{ticker.lower()}",
                revision_id="",
                period="2024Q3",
                formula_id=formula_id,
            )
        )
        return {
            "tool_id": self.manifest.tool_id,
            "status": "resolved",
            "formula_id": res.formula_id,
            "value": str(res.result.value) if res.result.value is not None else "",
            "unit": res.result.unit,
        }


class BctcTraceProvenanceDomainTool:
    manifest = TRACE_PROVENANCE_MANIFEST

    def __init__(self, manifest: ToolManifest | None = None, service: Any = None) -> None:
        self.manifest = manifest or TRACE_PROVENANCE_MANIFEST
        self.service = service
        self._underlying = BctcTraceProvenanceTool()

    async def execute(self, grant: ToolGrant) -> dict[str, str]:
        ticker, claim_ref = _parse_resource_ticker_and_item(
            getattr(grant, "resource_id", None), default_item="revenue"
        )
        res = self._underlying.execute(
            TraceProvenanceInput(
                report_id=f"report:{ticker.lower()}",
                revision_id="",
                claim_ref=claim_ref,
            )
        )
        return {
            "tool_id": self.manifest.tool_id,
            "status": "resolved",
            "claim_ref": res.claim_ref,
            "freshness_days": str(res.freshness_days),
        }


class BctcBuildEvidenceTableDomainTool:
    manifest = BUILD_EVIDENCE_TABLE_MANIFEST

    def __init__(self, manifest: ToolManifest | None = None, service: Any = None) -> None:
        self.manifest = manifest or BUILD_EVIDENCE_TABLE_MANIFEST
        self.service = service
        self._underlying = BctcBuildEvidenceTableTool()

    async def execute(self, grant: ToolGrant) -> dict[str, str]:
        ticker, claim_ref = _parse_resource_ticker_and_item(
            getattr(grant, "resource_id", None), default_item="revenue"
        )
        res = self._underlying.execute(
            BuildEvidenceTableInput(
                report_id=f"report:{ticker.lower()}",
                revision_id="",
                claim_refs=(claim_ref,),
            )
        )
        return {
            "tool_id": self.manifest.tool_id,
            "status": "resolved",
            "rows_count": str(len(res.rows)),
        }

