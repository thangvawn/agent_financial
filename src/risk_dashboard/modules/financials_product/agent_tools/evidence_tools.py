from __future__ import annotations

from risk_dashboard.modules.agentic_core.domain.tools import RiskClass, ToolGrant, ToolManifest
from risk_dashboard.modules.financials_product.agent_tools.helpers import (
    extract_ticker,
    get_line_item_val,
)
from risk_dashboard.modules.financials_product.application.report_resolver import ReportResolver
from risk_dashboard.modules.financials_product.schemas.agent_tools import (
    BuildEvidenceTableInput,
    BuildEvidenceTableOutput,
    EvidenceRow,
    NumericValue,
    TraceProvenanceInput,
    TraceProvenanceOutput,
    TransformStep,
)

TRACE_PROVENANCE_MANIFEST = ToolManifest(
    tool_id="bctc.trace_provenance",
    name="Trace Provenance of BCTC Data",
    module="financials_product",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Trace source provenance citations and transformation steps for a given claim.",
    required_capabilities=("bctc:report:read",),
)


class BctcTraceProvenanceTool:
    manifest = TRACE_PROVENANCE_MANIFEST

    def __init__(self, resolver: ReportResolver | None = None) -> None:
        self.resolver = resolver or ReportResolver()

    def execute(
        self,
        payload: TraceProvenanceInput,
        *,
        grant: ToolGrant | None = None,
        account_id: str = "",
    ) -> TraceProvenanceOutput:
        ticker = extract_ticker(payload.report_id)
        report_out = self.resolver.resolve_report(ticker)
        prov = self.resolver.make_provenance_ref(report_out, report_out.active_period)
        return TraceProvenanceOutput(
            schema_version="1.0.0",
            claim_ref=payload.claim_ref,
            citations=(prov,),
            transformation_chain=(
                TransformStep(
                    step="fetch",
                    detail=f"Fetched from official source {report_out.source}",
                ),
                TransformStep(
                    step="pin_revision",
                    detail=f"Pinned to revision {report_out.revision_id}",
                ),
            ),
            freshness_days=report_out.freshness_days,
        )


BUILD_EVIDENCE_TABLE_MANIFEST = ToolManifest(
    tool_id="bctc.build_evidence_table",
    name="Build BCTC Evidence Table",
    module="financials_product",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Build structured evidence rows from verified report line items and calculations.",
    required_capabilities=("bctc:evidence:read",),
)


class BctcBuildEvidenceTableTool:
    manifest = BUILD_EVIDENCE_TABLE_MANIFEST

    def __init__(self, resolver: ReportResolver | None = None) -> None:
        self.resolver = resolver or ReportResolver()

    def execute(
        self,
        payload: BuildEvidenceTableInput,
        *,
        grant: ToolGrant | None = None,
        account_id: str = "",
    ) -> BuildEvidenceTableOutput:
        ticker = extract_ticker(payload.report_id)
        report_out = self.resolver.resolve_report(ticker)
        dataset = self.resolver.load_dataset(ticker)
        period_data = self.resolver.get_period_data(dataset, report_out.active_period)

        rows: list[EvidenceRow] = []
        unsupported: list[str] = []

        for ref in payload.claim_refs:
            val = get_line_item_val(period_data, ref)
            if val is not None:
                prov = self.resolver.make_provenance_ref(
                    report_out,
                    report_out.active_period,
                    line_item=ref,
                )
                nv = NumericValue(
                    value=val,
                    unit="VND",
                    provenance=prov,
                    calculation_status="ok",
                )
                rows.append(
                    EvidenceRow(
                        claim=f"{ref} = {val}",
                        kind="fact",
                        value=nv,
                        citation=prov,
                    )
                )
            else:
                unsupported.append(ref)

        return BuildEvidenceTableOutput(
            schema_version="1.0.0",
            rows=tuple(rows),
            unsupported_claims=tuple(unsupported),
        )

