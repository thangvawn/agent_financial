"""Deterministic Market Summary report builder."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from risk_dashboard.modules.market_summary.domain.metrics import (
    calculate_capital_flow,
    calculate_index_metrics,
    calculate_market_breadth,
)
from risk_dashboard.modules.market_summary.domain.models import (
    DataQuality,
    MarketSummaryReport,
    ReportProvenance,
    StockContribution,
)
from risk_dashboard.modules.market_summary.domain.technical_analysis import calculate_technical_overview
from risk_dashboard.modules.market_summary.infrastructure.data_provider import FixtureMarketDataProvider, MarketDataProvider

LOCAL_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


class MarketSummarizer:
    def __init__(self, data_provider: MarketDataProvider) -> None:
        self.provider = data_provider

    def build_report(
        self,
        report_date: date,
        mode: str = "fast",
    ) -> MarketSummaryReport:
        now_dt = datetime.now(LOCAL_TZ)
        is_fixture = isinstance(self.provider, FixtureMarketDataProvider)

        # 1. Fetch indices
        df_vnindex = self.provider.get_index_history("VNINDEX", end_date=report_date)
        df_vn30 = self.provider.get_index_history("VN30", end_date=report_date)
        df_hnx = self.provider.get_index_history("HNXINDEX", end_date=report_date)

        vnindex_metrics = calculate_index_metrics("VN-Index", df_vnindex)
        vn30_metrics = calculate_index_metrics("VN30", df_vn30)
        hnx_metrics = calculate_index_metrics("HNX-Index", df_hnx)

        indices = [m for m in [vnindex_metrics, vn30_metrics, hnx_metrics] if m is not None]

        # 2. Market Breadth
        breadth_raw = self.provider.get_market_breadth(report_date)
        breadth = calculate_market_breadth(
            advancers=breadth_raw.get("advancers", 0),
            decliners=breadth_raw.get("decliners", 0),
            unchanged=breadth_raw.get("unchanged", 0),
            ceiling=breadth_raw.get("ceiling", 0),
            floor=breadth_raw.get("floor", 0),
        )

        # 3. Capital Flow
        foreign_df = self.provider.get_foreign_flow(report_date)
        capital_flow = calculate_capital_flow(foreign_df)

        # 4. Index Movers
        pos_raw, neg_raw = self.provider.get_index_movers(report_date)
        positive_movers = [StockContribution(ticker=m["ticker"], points_impact=m["points_impact"]) for m in pos_raw]
        negative_movers = [StockContribution(ticker=m["ticker"], points_impact=m["points_impact"]) for m in neg_raw]

        # 5. Technical Overview
        technical = calculate_technical_overview(df_vnindex) if mode == "analytical" else None

        # Data Quality
        quality = DataQuality(
            source="fixture" if is_fixture else "vnstock",
            fetched_at=now_dt,
            market_date=report_date,
            is_complete=True,
            is_stale=False,
            missing_fields=[] if capital_flow.is_available else ["foreign_flow"],
            warnings=["Using fixture simulated data."] if is_fixture else ([] if capital_flow.is_available else ["Foreign flow data currently unavailable."]),
        )

        provenance = ReportProvenance(
            schema_version="1.0",
            metrics_version="1.0",
            template_version="1.0",
            provider_name="fixture" if is_fixture else "vnstock",
            data_mode="fixture" if is_fixture else "live",
            environment="test" if is_fixture else "production",
        )

        return MarketSummaryReport(
            report_date=report_date,
            generated_at=now_dt,
            indices=indices,
            breadth=breadth,
            capital_flow=capital_flow,
            positive_movers=positive_movers,
            negative_movers=negative_movers,
            technical=technical,
            quality=quality,
            provenance=provenance,
        )
