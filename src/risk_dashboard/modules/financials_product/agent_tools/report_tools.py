from __future__ import annotations

from risk_dashboard.modules.agentic_core.domain.tools import RiskClass, ToolGrant, ToolManifest
from risk_dashboard.modules.financials_product.agent_tools.helpers import (
    extract_ticker,
    get_line_item_val,
)
from risk_dashboard.modules.financials_product.api.public import _line_item_explanations
from risk_dashboard.modules.financials_product.application.report_resolver import ReportResolver
from risk_dashboard.modules.financials_product.schemas.agent_tools import (
    NumericValue,
    ResolveLineItemInput,
    ResolveLineItemOutput,
    ResolveReportInput,
    ResolveReportOutput,
)

RESOLVE_REPORT_MANIFEST = ToolManifest(
    tool_id="bctc.resolve_report",
    name="Resolve BCTC Report",
    module="financials_product",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Fetch and pin report metadata, active revision, and available reporting periods for a ticker.",
    required_capabilities=("bctc:report:read",),
)


class BctcResolveReportTool:
    manifest = RESOLVE_REPORT_MANIFEST

    def __init__(self, resolver: ReportResolver | None = None) -> None:
        self.resolver = resolver or ReportResolver()

    def execute(
        self,
        payload: ResolveReportInput,
        *,
        grant: ToolGrant | None = None,
        account_id: str = "",
    ) -> ResolveReportOutput:
        return self.resolver.resolve_report(
            payload.ticker,
            period=payload.period,
            refresh=payload.refresh,
        )


RESOLVE_LINE_ITEM_MANIFEST = ToolManifest(
    tool_id="bctc.resolve_line_item",
    name="Resolve BCTC Line Item",
    module="financials_product",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Fetch a specific line item amount, provenance, definition and caveats from a report revision.",
    required_capabilities=("bctc:report:read",),
)


class BctcResolveLineItemTool:
    manifest = RESOLVE_LINE_ITEM_MANIFEST

    def __init__(self, resolver: ReportResolver | None = None) -> None:
        self.resolver = resolver or ReportResolver()

    def execute(
        self,
        payload: ResolveLineItemInput,
        *,
        grant: ToolGrant | None = None,
        account_id: str = "",
    ) -> ResolveLineItemOutput:
        ticker = extract_ticker(payload.report_id)
        report_out = self.resolver.resolve_report(ticker, period=payload.period)
        dataset = self.resolver.load_dataset(ticker)
        period_data = self.resolver.get_period_data(dataset, payload.period)

        val = get_line_item_val(period_data, payload.line_item)
        prov = self.resolver.make_provenance_ref(
            report_out,
            payload.period,
            statement="income_statement",
            line_item=payload.line_item,
        )
        status = "ok" if val is not None else "insufficient_data"
        amount = NumericValue(
            value=val,
            unit="VND",
            scale=1,
            calculation_status=status,
            provenance=prov,
        )

        explanations = _line_item_explanations()
        exp = explanations.get(payload.line_item, {})
        definition = exp.get("definition", f"Chỉ tiêu {payload.line_item} theo báo cáo tài chính.")
        caveat = exp.get("common_mistake")
        caveats = (caveat,) if caveat else ()

        return ResolveLineItemOutput(
            schema_version="1.0.0",
            line_item=payload.line_item,
            label_vi=payload.line_item,
            amount=amount,
            definition=definition,
            composition=(),
            caveats=caveats,
        )

