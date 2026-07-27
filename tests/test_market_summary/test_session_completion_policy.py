"""Unit tests for SessionCompletionPolicy."""

from __future__ import annotations

from datetime import date
from risk_dashboard.modules.market_summary.domain.policies import SessionCompletionPolicy


def test_session_completion_valid():
    policy = SessionCompletionPolicy(min_advancers_decliners_total=100)
    result = policy.validate(
        vnindex_latest_date=date(2026, 7, 27),
        expected_date=date(2026, 7, 27),
        vnindex_close=1295.0,
        vnindex_volume=750_000_000,
        total_breadth_stocks=460,
    )
    assert result.is_complete is True
    assert len(result.missing_fields) == 0


def test_session_completion_stale_date():
    policy = SessionCompletionPolicy()
    result = policy.validate(
        vnindex_latest_date=date(2026, 7, 26),
        expected_date=date(2026, 7, 27),
        vnindex_close=1295.0,
        vnindex_volume=750_000_000,
        total_breadth_stocks=460,
    )
    assert result.is_complete is False
    assert result.retry_recommended is True
    assert "trading_date" in result.missing_fields


def test_session_completion_missing_volume():
    policy = SessionCompletionPolicy()
    result = policy.validate(
        vnindex_latest_date=date(2026, 7, 27),
        expected_date=date(2026, 7, 27),
        vnindex_close=1295.0,
        vnindex_volume=0,
        total_breadth_stocks=460,
    )
    assert result.is_complete is False
    assert "vnindex_volume" in result.missing_fields
