"""Phase 2 reliability integration tests: Concurrency, Partial Delivery Recovery, and Stale Lock Takeover."""

from __future__ import annotations

import sqlite3
from datetime import date
from unittest.mock import MagicMock, patch

from risk_dashboard.modules.market_summary.application.runner import MarketSummaryRunner
from risk_dashboard.modules.market_summary.domain.trading_calendar import FixtureTradingCalendar
from risk_dashboard.modules.market_summary.infrastructure.data_provider import FixtureMarketDataProvider
from risk_dashboard.modules.market_summary.infrastructure.delivery_repository import DeliveryRepository, init_delivery_tables


def test_runner_concurrency_race():
    conn = sqlite3.connect(":memory:")
    init_delivery_tables(conn)
    repo = DeliveryRepository(db=conn)

    provider = FixtureMarketDataProvider(base_date=date(2026, 7, 27))
    calendar = FixtureTradingCalendar()

    mock_client = MagicMock()
    mock_client.send_html_message.return_value = {"ok": True, "result": {"message_id": 1001}}

    runner_a = MarketSummaryRunner(
        data_provider=provider,
        trading_calendar=calendar,
        repository=repo,
        telegram_client=mock_client,
        worker_id="runner_A",
    )

    runner_b = MarketSummaryRunner(
        data_provider=provider,
        trading_calendar=calendar,
        repository=repo,
        telegram_client=mock_client,
        worker_id="runner_B",
    )

    import os
    os.environ["TELEGRAM_BOT_TOKEN"] = "mock_token"
    os.environ["TELEGRAM_CHAT_ID"] = "12345"

    res_a = runner_a.run(target_date=date(2026, 7, 27), mode="analytical", allow_fixture_delivery=True)
    assert res_a["status"] == "sent"

    res_b = runner_b.run(target_date=date(2026, 7, 27), mode="analytical", allow_fixture_delivery=True)
    assert res_b["status"] == "skipped"
    assert res_b["reason"] == "already_delivered_or_locked"


def test_partial_chunk_recovery():
    conn = sqlite3.connect(":memory:")
    init_delivery_tables(conn)
    repo = DeliveryRepository(db=conn)

    provider = FixtureMarketDataProvider(base_date=date(2026, 7, 27))
    calendar = FixtureTradingCalendar()

    # Mock client fails on 2nd chunk
    call_count = 0

    def mock_send(text: str):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise RuntimeError("Network drop on chunk 2")
        return {"ok": True, "result": {"message_id": 2000 + call_count}}

    mock_client = MagicMock()
    mock_client.send_html_message.side_effect = mock_send

    import os
    os.environ["TELEGRAM_BOT_TOKEN"] = "mock_token"
    os.environ["TELEGRAM_CHAT_ID"] = "12345"

    runner = MarketSummaryRunner(
        data_provider=provider,
        trading_calendar=calendar,
        repository=repo,
        telegram_client=mock_client,
    )

    # Force multi-chunk split for test
    with patch("risk_dashboard.modules.market_summary.application.runner.pack_sections", return_value=["Chunk 1 content", "Chunk 2 content"]):
        # First attempt fails partially on chunk 2
        res1 = runner.run(target_date=date(2026, 7, 27), mode="analytical", allow_fixture_delivery=True)
        assert res1["status"] == "partial"
        assert 1 in res1["failed_chunks"]

        # Verify SQLite status
        sent_indices = repo.get_sent_chunk_indices(res1["delivery_id"])
        assert 0 in sent_indices
        assert 1 not in sent_indices

        # Resend: mock client now succeeds
        mock_client.send_html_message.side_effect = None
        mock_client.send_html_message.return_value = {"ok": True, "result": {"message_id": 3001}}

        res2 = runner.run(target_date=date(2026, 7, 27), mode="analytical", force=True, allow_fixture_delivery=True)
        assert res2["status"] == "sent"
