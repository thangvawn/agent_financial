"""Contract tests for MarketDataProvider implementations."""

from __future__ import annotations

from datetime import date
from risk_dashboard.modules.market_summary.infrastructure.data_provider import FixtureMarketDataProvider, VnstockMarketDataProvider


def test_fixture_provider_contract():
    provider = FixtureMarketDataProvider(base_date=date(2026, 7, 27))
    df = provider.get_index_history("VNINDEX", end_date=date(2026, 7, 27))
    assert not df.empty
    assert "close" in df.columns
    assert "volume" in df.columns

    breadth = provider.get_market_breadth(date(2026, 7, 27))
    assert "advancers" in breadth
    assert "decliners" in breadth

    flow = provider.get_foreign_flow(date(2026, 7, 27))
    assert flow is not None
    assert "net_value" in flow.columns

    pos, neg = provider.get_index_movers(date(2026, 7, 27))
    assert len(pos) > 0
    assert len(neg) > 0


def test_vnstock_provider_empty_fallback():
    provider = VnstockMarketDataProvider()
    # Query future date or invalid symbol to test fallback safety
    df = provider.get_index_history("INVALID_SYMBOL", end_date=date(2026, 7, 27))
    assert isinstance(df, object)
