"""Read public Yahoo quotes/history through the real producer, with temporary caches."""

from __future__ import annotations

import json
import argparse
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='output/qa/commodities-pipeline-review/public-provider.json')
    args = parser.parse_args()
    import yfinance as yf
    from risk_dashboard.modules.data_hub.application import global_market_feed as feed

    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="northstar-public-provider-review-") as directory:
        scratch = Path(directory)
        (scratch / "yfinance").mkdir()
        yf.set_tz_cache_location(str(scratch / "yfinance"))
        producer = feed.GlobalMarketFeedProducer(cache_dir=scratch / "feed")
        instruments = tuple(feed.find_instrument(symbol) for symbol in ["XAU", "WTI", "CORN"])
        downloads = []
        real_download = yf.download

        def capture_download(*args, **kwargs):
            frame = real_download(*args, **kwargs)
            samples = {}
            for instrument in instruments:
                series = feed._extract_close_series(frame, instrument.yahoo_symbol)
                samples[instrument.symbol] = [
                    {"date": str(index), "close": float(value)}
                    for index, value in series.tail(2).items()
                ]
            downloads.append(
                {
                    "period": kwargs.get("period"),
                    "interval": kwargs.get("interval"),
                    "index_timezone": str(frame.index.tz) if hasattr(frame.index, "tz") else None,
                    "samples": samples,
                }
            )
            return frame

        with (
            patch.object(feed, "GLOBAL_MARKET_INSTRUMENTS", instruments),
            patch.object(producer, "_fetch_crypto_snapshot_items", return_value=[]),
            patch.object(producer, "_fetch_vnstock_snapshot_items", return_value=[]),
            patch("yfinance.download", side_effect=capture_download),
        ):
            snapshot = producer.snapshot(force_refresh=True)
        print("Snapshot: " + str(len(snapshot["groups"]["commodities"])), flush=True)
        histories = []
        for instrument in instruments:
            history = producer.history(symbol=instrument.symbol, period="3mo", interval="1d")
            points = history.get("points", [])
            histories.append(
                {
                    "symbol": instrument.symbol,
                    "freshness": history.get("freshness"),
                    "points": len(points),
                    "first": points[0] if points else None,
                    "last": points[-1] if points else None,
                    "dates_ordered": all(a["date"] < b["date"] for a, b in zip(points, points[1:])),
                    "valid_ohlc": all(
                        p["low"]
                        <= min(p["open"], p["close"])
                        <= max(p["open"], p["close"])
                        <= p["high"]
                        for p in points
                    ),
                }
            )
            print(f"{instrument.symbol}: {len(points)} bars", flush=True)
        feed._MEM_HISTORY_CACHE.clear()
        exchange_timezones = {
            i.symbol: yf.cache.get_tz_cache().lookup(i.yahoo_symbol) for i in instruments
        }
    report = {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(time.monotonic() - started, 2),
        "temporary_runtime_removed": not scratch.exists(),
        "provider": "Yahoo Finance via installed yfinance " + yf.__version__,
        "snapshot": snapshot,
        "raw_snapshot_downloads": downloads,
        "exchange_timezones": exchange_timezones,
        "histories": histories,
    }
    path = ROOT / args.output
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
