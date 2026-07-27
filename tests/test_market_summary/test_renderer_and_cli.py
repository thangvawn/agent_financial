"""Unit tests for Market Summary Telegram HTML renderer and CLI runner."""

from __future__ import annotations

from datetime import date
from risk_dashboard.modules.market_summary.application.runner import MarketSummaryRunner
from risk_dashboard.modules.market_summary.application.summarizer import MarketSummarizer
from risk_dashboard.modules.market_summary.domain.trading_calendar import FixtureTradingCalendar
from risk_dashboard.modules.market_summary.infrastructure.data_provider import FixtureMarketDataProvider
from risk_dashboard.modules.market_summary.presentation.telegram_renderer import escape_html, pack_sections, render_report_sections


def test_escape_html():
    assert escape_html("VN-Index & VN30 < 1300 >") == "VN-Index &amp; VN30 &lt; 1300 &gt;"


def test_render_and_pack_sections():
    provider = FixtureMarketDataProvider(base_date=date(2026, 7, 27))
    summarizer = MarketSummarizer(provider)
    report = summarizer.build_report(report_date=date(2026, 7, 27), mode="analytical")

    sections = render_report_sections(report, mode="analytical")
    assert len(sections) >= 5

    chunks = pack_sections(sections, max_chars=3800)
    assert len(chunks) >= 1
    for chunk in chunks:
        assert len(chunk) <= 3800
        assert "TỔNG KẾT THỊ TRƯỜNG" in chunk or "GÓC NHÌN KỸ THUẬT" in chunk or "Dữ liệu cập nhật" in chunk


def test_runner_dry_run():
    provider = FixtureMarketDataProvider(base_date=date(2026, 7, 27))
    calendar = FixtureTradingCalendar()

    runner = MarketSummaryRunner(
        data_provider=provider,
        trading_calendar=calendar,
    )

    result = runner.run(
        target_date=date(2026, 7, 27),
        mode="analytical",
        dry_run=True,
    )

    assert result["status"] == "dry_run_success"
    assert result["chunks_count"] >= 1
    assert "TỔNG KẾT THỊ TRƯỜNG" in result["rendered_html"]
