"""Unit tests for Market Summary domain metrics and technical indicators."""

from __future__ import annotations

from datetime import date
import pandas as pd
from risk_dashboard.modules.market_summary.domain.metrics import (
    calculate_capital_flow,
    calculate_index_metrics,
    calculate_market_breadth,
)
from risk_dashboard.modules.market_summary.domain.technical_analysis import calculate_technical_overview
from risk_dashboard.modules.market_summary.infrastructure.data_provider import FixtureMarketDataProvider


def test_calculate_index_metrics():
    provider = FixtureMarketDataProvider(base_date=date(2026, 7, 27))
    df = provider.get_index_history("VNINDEX", end_date=date(2026, 7, 27))

    metrics = calculate_index_metrics("VN-Index", df)
    assert metrics is not None
    assert metrics.symbol == "VN-Index"
    assert metrics.close > 0
    assert metrics.change_pct != 0
    assert metrics.volume > 0
    assert metrics.vol_vs_prev_pct is not None
    assert metrics.vol_vs_sma20_pct is not None


def test_calculate_market_breadth():
    breadth = calculate_market_breadth(285, 122, 53, ceiling=12, floor=2)
    assert breadth.advancers == 285
    assert breadth.decliners == 122
    assert "lan tỏa tích cực" in breadth.summary_assessment


def test_calculate_capital_flow():
    foreign_df = pd.DataFrame(
        [
            {"symbol": "FPT", "net_value": 150_000_000_000.0},
            {"symbol": "MWG", "net_value": 85_000_000_000.0},
            {"symbol": "VHM", "net_value": -120_000_000_000.0},
        ]
    )
    flow = calculate_capital_flow(foreign_df)
    assert flow.is_available is True
    assert flow.net_foreign_val_billion == 115.0  # (150 + 85 - 120) / 10 = 115
    assert len(flow.top_foreign_buy) == 2
    assert flow.top_foreign_buy[0][0] == "FPT"
    assert len(flow.top_foreign_sell) == 1
    assert flow.top_foreign_sell[0][0] == "VHM"


def test_calculate_technical_overview():
    provider = FixtureMarketDataProvider(base_date=date(2026, 7, 27))
    df = provider.get_index_history("VNINDEX", end_date=date(2026, 7, 27))

    tech = calculate_technical_overview(df)
    assert tech is not None
    assert tech.short_term_trend in ["BULLISH", "BEARISH", "NEUTRAL_SIDEWAYS"]
    assert tech.support_zone[0] < tech.support_zone[1]
    assert tech.resistance_zone[0] < tech.resistance_zone[1]
    assert len(tech.watch_points) >= 2
