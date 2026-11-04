"""Regression contracts for the November commodity pipeline review.

Run via scripts/qa/run_isolated_tests.py. All provider calls and cache paths
are replaced before invoking the real API; the application's DB is never used.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Event
from unittest.mock import patch

import pandas as pd
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from risk_dashboard.modules.data_hub.api.public import router as history_router
from risk_dashboard.modules.data_hub.application import global_market_feed as feed
from risk_dashboard.modules.data_hub.application import services
from risk_dashboard.modules.market_portfolio.api.public import router as quote_router
from risk_dashboard.modules.market_portfolio.application import commodity_feed
from risk_dashboard.platform.database.config import clear_db_path_cache
from risk_dashboard.platform.database.connection import open_db

QUOTES = "/api/v1/market-portfolio/market-data/commodities/snapshot"
HISTORY = "/api/v1/public/data-hub/instruments/XAU/history?period=3mo&interval=1d"


@pytest.fixture
def setup(tmp_path, monkeypatch):
    for key in ("RISK_DASHBOARD_DB_PATH", "RISK_DASHBOARD_APP_STATE_DB", "RISK_DASHBOARD_SQLITE"):
        monkeypatch.setenv(key, str(tmp_path / "state.db"))
    clear_db_path_cache()
    producer = feed.GlobalMarketFeedProducer(cache_dir=tmp_path / "cache")
    instruments = tuple(feed.find_instrument(s) for s in ["XAU", "WTI", "CORN"])
    monkeypatch.setattr(feed, "GLOBAL_MARKET_INSTRUMENTS", instruments)
    monkeypatch.setattr(commodity_feed, "GlobalMarketFeedProducer", lambda **kw: producer)
    monkeypatch.setattr(services, "GlobalMarketFeedProducer", lambda **kw: producer)
    monkeypatch.setattr(producer, "refresh_in_background", lambda: False)
    monkeypatch.setattr(producer, "_fetch_vnstock_snapshot_items", lambda: [])
    monkeypatch.setattr(producer, "_fetch_crypto_snapshot_items", lambda: [])
    monkeypatch.setattr(
        feed, "_exchange_timezone", lambda instrument: "America/New_York", raising=False
    )
    monkeypatch.setattr("yfinance.download", lambda *a, **kw: pytest.fail("Unexpected network"))
    monkeypatch.setattr(
        "requests.sessions.Session.request", lambda *a, **kw: pytest.fail("Unexpected network")
    )
    app = FastAPI()
    app.include_router(history_router, prefix="/api/v1/public")
    app.include_router(quote_router, prefix="/api/v1")
    yield producer, TestClient(app), instruments
    clear_db_path_cache()


def quote(symbol="XAU", *, age=0, price=100):
    stamp = (datetime.now(timezone.utc) - timedelta(seconds=age)).isoformat()
    return {
        "symbol": symbol,
        "group": "commodities",
        "price": price,
        "change_pct": 1,
        "updated_at": stamp,
        "fetched_at": stamp,
        "source": "yahoo_finance",
    }


def write_snapshot(producer, items, *, age=0):
    producer._write_cache(
        {"as_of": (datetime.now(timezone.utc) - timedelta(seconds=age)).isoformat(), "items": items}
    )


def frame():
    return pd.DataFrame(
        {
            "Open": [100.0, 101.0],
            "High": [103.0, 104.0],
            "Low": [99.0, 100.0],
            "Close": [102.0, 103.0],
            "Volume": [10.0, 20.0],
        },
        index=pd.to_datetime(["2026-11-01", "2026-11-02"]),
    )


def test_previous_close_uses_exchange_date_and_keeps_unknown_reference(setup, monkeypatch):
    producer, client, instruments = setup
    monkeypatch.setattr(feed, "GLOBAL_MARKET_INSTRUMENTS", instruments[:1])
    daily = pd.DataFrame(
        {"Close": [90.0, 100.0]}, index=pd.to_datetime(["2026-10-30", "2026-11-02"])
    )
    intraday = frame()
    intraday["Close"] = [100.0, 101.0]
    intraday.index = pd.to_datetime(["2026-11-03T01:00Z", "2026-11-03T01:05Z"])
    with patch("yfinance.download", side_effect=[daily, intraday]):
        producer.snapshot(force_refresh=True)
    row = client.get(QUOTES).json()["items"][0]
    assert row["change_pct"] == pytest.approx(12.222, abs=0.001)
    assert row["reference_price"] == 90
    with patch("yfinance.download", side_effect=[pd.DataFrame(), intraday]):
        producer.snapshot(force_refresh=True)
    row = client.get(QUOTES).json()["items"][0]
    assert row["price"] == 101
    assert row["change_pct"] is None and row["reference_price"] is None


def test_session_extrema_exclude_previous_local_day(setup, monkeypatch):
    producer, client, instruments = setup
    monkeypatch.setattr(feed, "GLOBAL_MARKET_INSTRUMENTS", instruments[:1])
    daily = frame()
    bars = pd.DataFrame(
        {
            "Open": [100.0, 100.0, 100.0],
            "High": [999.0, 110.0, 102.0],
            "Low": [1.0, 80.0, 99.0],
            "Close": [100.0, 100.0, 101.0],
            "Volume": [999.0, 100.0, 200.0],
        },
        index=pd.to_datetime(["2026-11-02T02:00Z", "2026-11-02T18:00Z", "2026-11-03T01:05Z"]),
    )
    with patch("yfinance.download", side_effect=[daily, bars]):
        producer.snapshot(force_refresh=True)
    row = client.get(QUOTES).json()["items"][0]
    assert (row["high_24h"], row["low_24h"], row["volume_24h"]) == (110, 80, 300)
    assert row["statistics_window"] == "exchange_day"


def test_partial_snapshot_keeps_missing_contracts_and_marks_coverage(setup, monkeypatch):
    producer, client, _ = setup
    write_snapshot(producer, [quote(), quote("WTI")])
    assert client.get(QUOTES).status_code == 200
    monkeypatch.setattr(
        producer,
        "_fetch_yahoo_snapshot",
        lambda: {
            "as_of": datetime.now(timezone.utc).isoformat(),
            "items": [quote("WTI", price=105)],
        },
    )
    producer.snapshot(force_refresh=True)
    data = client.get(QUOTES).json()
    rows = {r["symbol"]: r for r in data["items"]}
    assert set(rows) == {"XAU", "WTI", "CORN"}
    assert rows["XAU"]["price"] == 100 and rows["XAU"]["quote_status"] == "stale"
    assert rows["WTI"]["price"] == 105
    assert rows["CORN"]["price"] is None and rows["CORN"]["quote_status"] == "unavailable"
    assert data["freshness"] != "fresh" and data["coverage"]["quoted"] == 2


def test_crypto_refresh_and_db_fallback_preserve_real_quote_time(setup, monkeypatch):
    producer, client, _ = setup
    old = quote(age=7 * 86400)
    write_snapshot(producer, [old], age=7 * 86400)
    client.get(QUOTES)
    with open_db() as conn:
        before = conn.execute("SELECT count(*) FROM commodity_quotes").fetchone()[0]
    monkeypatch.setattr(
        producer,
        "_fetch_crypto_snapshot_items",
        lambda: [{**quote(), "symbol": "BTC", "group": "crypto"}],
    )
    done = Event()
    original = producer._write_cache

    def written(payload):
        original(payload)
        done.set()

    monkeypatch.setattr(producer, "_write_cache", written)
    assert producer.refresh_crypto_in_background()
    assert done.wait(5)
    data = client.get(QUOTES).json()
    row = next(r for r in data["items"] if r["symbol"] == "XAU")
    assert data["freshness"] != "fresh"
    assert row["updated_at"] == old["updated_at"] and row["quote_status"] == "stale"
    with open_db() as conn:
        assert conn.execute("SELECT count(*) FROM commodity_quotes").fetchone()[0] == before
    write_snapshot(producer, [])
    fallback = client.get(QUOTES).json()
    row = next(r for r in fallback["items"] if r["symbol"] == "XAU")
    assert row["updated_at"] == old["updated_at"] and row["quote_status"] == "stale"
    assert fallback["freshness"] != "fresh"


def test_history_refresh_reaches_provider_and_throttles_repeated_clicks(setup):
    _, client, _ = setup
    changed = frame() * 2
    with patch("yfinance.download", side_effect=[frame(), changed]) as download:
        first = client.get(HISTORY)
        second = client.get(HISTORY + "&refresh=true")
        third = client.get(HISTORY + "&refresh=true")
    assert first.status_code == second.status_code == third.status_code == 200
    assert first.json()["points"][-1]["close"] == 103
    assert second.json()["points"][-1]["close"] == 206
    assert download.call_count == 2
    assert third.json()["refresh_status"] == "throttled"


def test_history_failure_keeps_last_good_payload(setup):
    _, client, _ = setup
    with patch("yfinance.download", side_effect=[frame(), RuntimeError("provider down")]):
        first = client.get(HISTORY).json()
        failed = client.get(HISTORY + "&refresh=true").json()
    assert failed["points"] == first["points"]
    assert failed["freshness"] == "stale" and failed["refresh_status"] == "failed"


def test_history_cache_is_scoped_to_directory(setup, tmp_path):
    producer, _, _ = setup
    with patch("yfinance.download", return_value=frame()):
        producer.history(symbol="XAU", period="3mo")
    other = feed.GlobalMarketFeedProducer(cache_dir=tmp_path / "other")
    with patch("yfinance.download", return_value=frame() * 2) as download:
        result = other.history(symbol="XAU", period="3mo")
    assert download.call_count == 1 and result["points"][-1]["close"] == 206


def test_same_history_requests_share_provider_work(setup):
    producer, _, _ = setup
    entered, release = Event(), Event()

    def download(*a, **kw):
        entered.set()
        assert release.wait(5)
        return frame()

    with (
        patch("yfinance.download", side_effect=download) as fetch,
        ThreadPoolExecutor(max_workers=2) as pool,
    ):
        first = pool.submit(producer.history, symbol="XAU", period="3mo")
        assert entered.wait(5)
        second = pool.submit(producer.history, symbol="XAU", period="3mo")
        release.set()
        assert first.result()["points"] == second.result()["points"]
        assert fetch.call_count == 1


def test_parallel_periods_cannot_overwrite_yfinance_shared_state(setup):
    producer, _, _ = setup
    import yfinance as yf
    from yfinance import multi, shared

    # The fixture replaced yf.download; get the real installed implementation.
    download = multi.download
    first_entered, second_entered, release = Event(), Event(), Event()

    def leaf(ticker, *, period, **kw):
        shared._DFS[ticker] = frame() if period == "1mo" else frame() * 2
        if period == "1mo":
            first_entered.set()
            assert release.wait(5)
        else:
            second_entered.set()
        return shared._DFS[ticker]

    with (
        patch.object(yf, "download", download),
        patch.object(multi, "_download_one", side_effect=leaf),
        ThreadPoolExecutor(max_workers=2) as pool,
    ):
        short = pool.submit(producer.history, symbol="XAU", period="1mo")
        assert first_entered.wait(5)
        long = pool.submit(producer.history, symbol="XAU", period="3mo")
        overlapped = second_entered.wait(0.2)
        release.set()
        a, b = short.result(), long.result()
    assert not overlapped
    assert a["points"][-1]["close"] == 103 and b["points"][-1]["close"] == 206
