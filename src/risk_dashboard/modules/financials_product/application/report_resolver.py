from __future__ import annotations

from typing import Sequence

from risk_dashboard.data.financials import get_financial_dataset
from risk_dashboard.modules.financials_product.domain.ports import ReportReader
from risk_dashboard.modules.financials_product.domain.provenance import (
    calculate_freshness_days,
    derive_revision_id,
)
from risk_dashboard.modules.financials_product.schemas.agent_tools import (
    ProvenanceRef,
    ResolveReportOutput,
)
from risk_dashboard.schemas.financials import FinancialDataset, FinancialPeriodData


class ReportResolver(ReportReader):
    """Resolves and pins financial reports to deterministic revisions."""

    def load_dataset(self, ticker: str, refresh: bool = False) -> FinancialDataset:
        return get_financial_dataset(ticker, refresh=refresh)

    def resolve_report(
        self,
        ticker: str,
        period: str | None = None,
        refresh: bool = False,
    ) -> ResolveReportOutput:
        dataset = self.load_dataset(ticker, refresh=refresh)
        periods = tuple(p.period for p in dataset.periods)
        fetched_at_iso = dataset.fetched_at.isoformat()
        revision_id = derive_revision_id(dataset.source, fetched_at_iso, periods)
        active_period = period if period and period in periods else (periods[-1] if periods else "")
        report_id = f"report:{dataset.ticker.lower()}"
        freshness = calculate_freshness_days(fetched_at_iso)

        return ResolveReportOutput(
            schema_version="1.0.0",
            report_id=report_id,
            revision_id=revision_id,
            ticker=dataset.ticker,
            company_name=dataset.company_name,
            exchange=dataset.exchange,
            available_periods=periods,
            active_period=active_period,
            currency="VND",
            source=dataset.source,
            fetched_at=fetched_at_iso,
            freshness_days=freshness,
            is_private_upload=False,
        )

    def get_period_data(
        self,
        dataset: FinancialDataset,
        period_str: str,
    ) -> FinancialPeriodData | None:
        for p in dataset.periods:
            if p.period == period_str:
                return p
        return None

    def make_provenance_ref(
        self,
        report_out: ResolveReportOutput,
        period: str,
        *,
        statement: str | None = None,
        line_item: str | None = None,
    ) -> ProvenanceRef:
        valid_statement = statement if statement in ("income_statement", "balance_sheet", "cash_flow") else None
        return ProvenanceRef(
            report_id=report_out.report_id,
            revision_id=report_out.revision_id,
            period=period,
            source=report_out.source,
            fetched_at=report_out.fetched_at,
            statement=valid_statement,  # type: ignore
            line_item=line_item,
        )

