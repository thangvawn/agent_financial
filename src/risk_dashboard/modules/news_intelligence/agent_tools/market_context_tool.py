from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from risk_dashboard.modules.agentic_core.schemas.envelope import TrustedExecutionEnvelope
from risk_dashboard.modules.market_summary.application.summarizer import MarketSummarizer
from risk_dashboard.modules.market_summary.infrastructure.data_provider import FixtureMarketDataProvider
from risk_dashboard.modules.news_intelligence.agent_tools.helpers import check_scope
from risk_dashboard.modules.news_intelligence.domain.entities import utc_now_iso
from risk_dashboard.modules.news_intelligence.schemas.agent_tools import (
    GetMarketContextInput,
    GetMarketContextOutput,
)


async def get_market_context(
    payload: GetMarketContextInput,
    envelope: TrustedExecutionEnvelope,
) -> GetMarketContextOutput:
    check_scope(envelope, ("public:market_summary:read", "public:news:read", "public:news:agent:read"))

    now_dt = datetime.now(timezone.utc)
    time_aligned = True
    ev_dt = now_dt
    try:
        ev_dt = datetime.fromisoformat(payload.event_time)
        delta_hours = abs((now_dt - ev_dt).total_seconds()) / 3600.0
        if delta_hours > 48:
            time_aligned = False
    except (ValueError, TypeError):
        time_aligned = False

    try:
        provider = FixtureMarketDataProvider()
        summarizer = MarketSummarizer(data_provider=provider)
        report = summarizer.build_report(report_date=ev_dt.date())

        idx_list: list[dict[str, Any]] = []
        for idx in report.indices:
            idx_list.append({
                "symbol": idx.symbol,
                "close": idx.close,
                "change_points": idx.change_points,
                "change_pct": idx.change_pct,
                "volume": idx.volume,
                "value_vnd": idx.value_vnd,
            })

        breadth_dict = None
        if report.breadth:
            breadth_dict = {
                "advancers": report.breadth.advancers,
                "decliners": report.breadth.decliners,
                "unchanged": report.breadth.unchanged,
                "summary_assessment": report.breadth.summary_assessment,
            }

        cap_dict = None
        if report.capital_flow:
            cap_dict = {
                "net_foreign_val_billion": report.capital_flow.net_foreign_val_billion,
                "top_foreign_buy": report.capital_flow.top_foreign_buy,
                "top_foreign_sell": report.capital_flow.top_foreign_sell,
            }

        data_quality: Literal["complete", "partial", "stale", "unavailable"] = "complete" if time_aligned else "stale"

        return GetMarketContextOutput(
            schema_version="1.0.0",
            as_of=utc_now_iso(),
            session_state="closed",
            index_metrics=tuple(idx_list),
            breadth=breadth_dict,
            capital_flow=cap_dict,
            data_quality=data_quality,
            provenance={
                "source": "market_summary",
                "version": report.provenance.metrics_version if report.provenance else "1.0.0",
                "event_time": payload.event_time,
            },
            time_aligned=time_aligned,
        )
    except Exception:
        return GetMarketContextOutput(
            schema_version="1.0.0",
            as_of=utc_now_iso(),
            session_state="closed",
            index_metrics=(),
            breadth=None,
            capital_flow=None,
            data_quality="unavailable",
            provenance={
                "source": "market_summary",
                "version": "1.0.0",
                "event_time": payload.event_time,
            },
            time_aligned=False,
        )
