"""Reproduce commodity pipeline review findings using temporary DB/cache only.

This is an observation harness, not a regression suite asserting fixed behavior.
It refuses provider network access and writes evidence under output/qa/.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "output/qa/commodities-pipeline-review"
sys.path.insert(0, str(ROOT / "src"))


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    findings = []
    with tempfile.TemporaryDirectory(prefix="northstar-commodity-review-") as directory:
        scratch = Path(directory)
        os.environ.update(
            {
                "PYTHON_DOTENV_DISABLED": "1",
                "RISK_DASHBOARD_DB_PATH": str(scratch / "state.db"),
                "RISK_DASHBOARD_APP_STATE_DB": str(scratch / "state.db"),
                "RISK_DASHBOARD_SQLITE": str(scratch / "state.db"),
                "ENABLE_VN_MARKET_SCHEDULER": "0",
                "ENABLE_SOCIAL_WORKER": "0",
                "ENABLE_TELEGRAM_NEWS_SCHEDULER": "0",
                "ENABLE_VN_SCREENER": "0",
                "VN_SCREENER_CACHE_DIR": str(scratch / "screener"),
            }
        )
        import pandas as pd
        import yfinance as yf
        from concurrent.futures import ThreadPoolExecutor
        from threading import Event
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from risk_dashboard.modules.data_hub.application import global_market_feed as feed
        from risk_dashboard.modules.data_hub.application import services
        from risk_dashboard.modules.data_hub.api.public import router as history_router
        from risk_dashboard.modules.market_portfolio.application import commodity_feed
        from risk_dashboard.modules.market_portfolio.api.public import router as quote_router

        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        old = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        gold = {
            "symbol": "XAU",
            "name": "Gold",
            "yahoo_symbol": "GC=F",
            "group": "commodities",
            "category": "metals",
            "unit": "USD/oz",
            "price": 100,
            "change_pct": 1,
            "updated_at": old,
        }
        oil = {
            **gold,
            "symbol": "WTI",
            "name": "Oil",
            "yahoo_symbol": "CL=F",
            "category": "energy",
            "unit": "USD/bbl",
        }
        btc = {
            "symbol": "BTC",
            "group": "crypto",
            "price": 1000,
            "change_pct": 1,
            "updated_at": now,
        }
        producer = feed.GlobalMarketFeedProducer(cache_dir=scratch / "feed")
        real_download = yf.download
        app = FastAPI()
        app.include_router(history_router, prefix="/api/v1/public")
        app.include_router(quote_router, prefix="/api/v1")
        client = TestClient(app, raise_server_exceptions=False)
        quote_url = "/api/v1/market-portfolio/market-data/commodities/snapshot"
        history_url = "/api/v1/public/data-hub/instruments/XAU/history?period=3mo&interval=1d"

        def save(name, **details):
            findings.append({"case": name, **details})

        with ExitStack() as stack:
            stack.enter_context(
                patch(
                    "requests.sessions.Session.request",
                    side_effect=AssertionError("Review forbids network"),
                )
            )
            stack.enter_context(
                patch(
                    "yfinance.download",
                    side_effect=AssertionError("Review requires provider fixture"),
                )
            )
            stack.enter_context(
                patch.object(commodity_feed, "GlobalMarketFeedProducer", lambda **kwargs: producer)
            )
            stack.enter_context(
                patch.object(services, "GlobalMarketFeedProducer", lambda **kwargs: producer)
            )
            stack.enter_context(
                patch.object(
                    feed.GlobalMarketFeedProducer, "refresh_in_background", return_value=False
                )
            )

            producer._write_cache({"as_of": old, "items": [gold, oil]})
            assert client.get(quote_url).status_code == 200
            with patch.object(
                producer,
                "_fetch_yahoo_snapshot",
                return_value={"as_of": now, "items": [{**oil, "price": 105, "updated_at": now}]},
            ):
                producer.snapshot(force_refresh=True)
            partial = client.get(quote_url).json()
            assert [row["symbol"] for row in partial["items"]] == ["WTI"]
            save(
                "partial_provider_drops_cached_contract",
                freshness=partial["freshness"],
                returned=[row["symbol"] for row in partial["items"]],
                missing="XAU",
                db_has_previous_quote=True,
            )

            producer._write_cache({"as_of": old, "items": [gold, oil]})

            class InlineThread:
                def __init__(self, *, target, **kwargs):
                    self.target = target

                def start(self):
                    self.target()

            with (
                patch.object(producer, "_fetch_crypto_snapshot_items", return_value=[btc]),
                patch.object(feed.threading, "Thread", InlineThread),
            ):
                producer.refresh_crypto_in_background()
            crypto = client.get(quote_url).json()
            assert crypto["freshness"] == "fresh" and crypto["items"][0]["updated_at"] == old
            save(
                "crypto_refresh_marks_week_old_commodities_fresh",
                freshness=crypto["freshness"],
                response_as_of=crypto["as_of"],
                quote_updated_at=crypto["items"][0]["updated_at"],
            )

            producer._write_cache({"as_of": now, "items": [btc]})
            fallback = client.get(quote_url).json()
            assert fallback["items"] and fallback["freshness"] == "fresh"
            assert all("updated_at" not in row for row in fallback["items"])
            save(
                "db_fallback_reports_fresh_and_loses_provider_time",
                freshness=fallback["freshness"],
                item_count=len(fallback["items"]),
                quote_updated_at_present=False,
                item_as_of=fallback["items"][0]["as_of"],
            )

            frame = pd.DataFrame(
                {
                    "Open": [100.0, 101.0],
                    "High": [103.0, 104.0],
                    "Low": [99.0, 100.0],
                    "Close": [102.0, 103.0],
                    "Volume": [10.0, float("nan")],
                },
                index=pd.to_datetime(["2026-11-01", "2026-11-02"]),
            )
            feed._MEM_HISTORY_CACHE.clear()
            producer = feed.GlobalMarketFeedProducer(cache_dir=scratch / "missing-volume")
            with patch("yfinance.download", return_value=frame) as download:
                first = client.get(history_url)
                second = client.get(history_url)
            assert first.status_code == second.status_code
            assert download.call_count == 1
            save(
                "missing_volume_history_serialization",
                first_http=first.status_code,
                cached_http=second.status_code,
                provider_calls=download.call_count,
                response=first.json() if first.status_code == 200 else first.text,
            )

            producer = feed.GlobalMarketFeedProducer(cache_dir=scratch / "intraday")
            daily = pd.DataFrame(
                {"Close": [90.0, 100.0]}, index=pd.to_datetime(["2026-10-30", "2026-11-02"])
            )
            intraday = pd.DataFrame(
                {
                    "Open": [99.0, 100.0],
                    "High": [110.0, 102.0],
                    "Low": [80.0, 99.0],
                    "Close": [100.0, 101.0],
                    "Volume": [100.0, 200.0],
                },
                index=pd.to_datetime(["2026-11-02T18:00:00Z", "2026-11-02T18:05:00Z"]),
            )
            instrument = feed.find_instrument("XAU")
            with (
                patch.object(feed, "GLOBAL_MARKET_INSTRUMENTS", (instrument,)),
                patch("yfinance.download", side_effect=[daily, intraday]),
                patch.object(producer, "_fetch_crypto_snapshot_items", return_value=[]),
                patch.object(producer, "_fetch_vnstock_snapshot_items", return_value=[]),
            ):
                producer.snapshot(force_refresh=True)
            stats = client.get(quote_url).json()["items"][0]
            assert stats["high_24h"] == 102 and stats["low_24h"] == 99
            save(
                "session_high_low_use_only_final_5m_bar",
                returned_high=stats["high_24h"],
                returned_low=stats["low_24h"],
                session_high=110,
                session_low=80,
                session_volume=stats["volume_24h"],
            )

            # Yahoo daily bars are naive exchange-local dates; intraday uses UTC.
            # 01:00 UTC is still Nov 2 in New York for this commodity contract.
            late = intraday.copy()
            late.index = pd.to_datetime(["2026-11-03T01:00:00Z", "2026-11-03T01:05:00Z"])
            with (
                patch.object(feed, "GLOBAL_MARKET_INSTRUMENTS", (instrument,)),
                patch("yfinance.download", side_effect=[daily, late]),
                patch.object(producer, "_fetch_crypto_snapshot_items", return_value=[]),
                patch.object(producer, "_fetch_vnstock_snapshot_items", return_value=[]),
            ):
                producer.snapshot(force_refresh=True)
            late_stats = client.get(quote_url).json()["items"][0]
            assert late_stats["change_pct"] == 1.0
            save(
                "previous_close_compares_exchange_date_with_utc_date",
                daily_current_date="2026-11-02",
                quote_utc_date="2026-11-03",
                quote_exchange_date="2026-11-02",
                previous_completed_daily_close=90,
                current_daily_close=100,
                current_price=101,
                returned_change_pct=late_stats["change_pct"],
                expected_previous_daily_change_pct=round((101 - 90) / 90 * 100, 3),
            )

            producer = feed.GlobalMarketFeedProducer(cache_dir=scratch / "history-refresh")
            healthy_frame = frame.fillna({"Volume": 0})
            feed._MEM_HISTORY_CACHE.clear()
            with patch("yfinance.download", return_value=healthy_frame) as download:
                first = client.get(history_url)
                second = client.get(history_url + "&refresh=true")
            assert first.status_code == second.status_code == 200 and download.call_count == 1
            save(
                "history_endpoint_has_no_force_refresh",
                first_http=first.status_code,
                second_http=second.status_code,
                provider_calls=download.call_count,
                equal_payload=first.json() == second.json(),
            )

            # Distinct instances with distinct cache directories must not share data.
            other = feed.GlobalMarketFeedProducer(cache_dir=scratch / "other-history")
            with patch.object(
                other, "_fetch_yahoo_history", return_value={"as_of": now, "points": []}
            ) as fetch:
                result = other.history(symbol="XAU", period="3mo", interval="1d")
            assert result["points"] and fetch.call_count == 0
            save(
                "history_memory_cache_crosses_directory_boundary",
                provider_calls=fetch.call_count,
                leaked_points=len(result["points"]),
            )

            # Exercise the installed yfinance download implementation concurrently.
            # Only its network leaf is substituted; both producer.history calls are real.
            from yfinance import multi, shared

            feed._MEM_HISTORY_CACHE.clear()
            concurrent_producer = feed.GlobalMarketFeedProducer(cache_dir=scratch / "concurrent")
            first_download_waiting, second_history_finished = Event(), Event()
            short = healthy_frame.copy()
            earlier = healthy_frame.iloc[:1].copy()
            earlier.index = pd.to_datetime(["2026-09-01"])
            long = pd.concat([earlier, healthy_frame])

            def download_one(ticker, *, period, **kwargs):
                result = short.copy() if period == "1mo" else long.copy()
                shared._DFS[ticker] = result
                if period == "1mo":
                    first_download_waiting.set()
                    assert second_history_finished.wait(10)
                return result

            with (
                patch("yfinance.download", real_download),
                patch.object(multi, "_download_one", side_effect=download_one),
                ThreadPoolExecutor(max_workers=2) as pool,
            ):
                short_future = pool.submit(
                    concurrent_producer.history, symbol="XAU", period="1mo", interval="1d"
                )
                assert first_download_waiting.wait(10)
                try:
                    long_result = concurrent_producer.history(
                        symbol="XAU", period="3mo", interval="1d"
                    )
                finally:
                    second_history_finished.set()
                short_result = short_future.result(timeout=10)
            assert short_result["points"] == long_result["points"]
            assert short_result["points"][0]["date"].startswith("2026-09-01")
            save(
                "parallel_yfinance_histories_contaminate_each_other",
                yfinance_version=yf.__version__,
                one_month_expected_points=len(short),
                one_month_actual_points=len(short_result["points"]),
                incorrect_first_date=short_result["points"][0]["date"],
                equal_to_three_month_history=True,
            )

            # Healthy serialization, sorted dates and DB fallback are also exercised.
            points = first.json()["points"]
            assert points[0]["date"] < points[1]["date"]
            save(
                "healthy_history_api", http=first.status_code, points=len(points), dates_sorted=True
            )

        # Copy public snapshot metadata only; do not open the application's DB.
        source_path = ROOT / "data/global_market_prices/global_market_snapshot.json"
        live = json.loads(source_path.read_text())
        live_rows = [row for row in live.get("items", []) if row.get("group") == "commodities"]
        save(
            "current_public_snapshot_observation",
            as_of=live.get("as_of"),
            contracts=len(live_rows),
            unique_symbols=len({row["symbol"] for row in live_rows}),
            missing_prices=sum(row.get("price") is None for row in live_rows),
            oldest_quote=min((row.get("updated_at", "") for row in live_rows), default=""),
            newest_quote=max((row.get("updated_at", "") for row in live_rows), default=""),
        )
        feed._MEM_HISTORY_CACHE.clear()
    report = {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "temporary_runtime_removed": not scratch.exists(),
        "application_source_changed": False,
        "observations": findings,
    }
    path = OUTPUT / "backend-observations.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
