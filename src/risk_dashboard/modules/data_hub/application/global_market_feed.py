from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any

import pandas as pd


_PROJECT_ROOT = Path(__file__).resolve().parents[5]
GLOBAL_MARKET_CACHE_DIR = _PROJECT_ROOT / "data" / "global_market_prices"


@dataclass(frozen=True)
class FeedInstrument:
    symbol: str
    name: str
    yahoo_symbol: str
    group: str
    focus: str


GLOBAL_MARKET_INSTRUMENTS: tuple[FeedInstrument, ...] = (
    FeedInstrument("SPX", "S&P 500", "^GSPC", "indices", "US large-cap breadth"),
    FeedInstrument("NDX", "Nasdaq 100", "^NDX", "indices", "US growth / tech beta"),
    FeedInstrument("RUT", "Russell 2000", "^RUT", "indices", "US small-cap risk appetite"),
    FeedInstrument("DAX", "DAX", "^GDAXI", "indices", "Europe growth pulse"),
    FeedInstrument("FTSE", "FTSE 100", "^FTSE", "indices", "UK defensive mix"),
    FeedInstrument("NIKKEI", "Nikkei 225", "^N225", "indices", "Japan equity pulse"),
    FeedInstrument("HANGSENG", "Hang Seng", "^HSI", "indices", "China/HK sentiment"),
    FeedInstrument("DXY", "Dollar Index", "DX-Y.NYB", "fx", "USD pressure"),
    FeedInstrument("EURUSD", "EUR/USD", "EURUSD=X", "fx", "Europe vs USD"),
    FeedInstrument("USDJPY", "USD/JPY", "JPY=X", "fx", "JPY carry stress"),
    FeedInstrument("AUDUSD", "AUD/USD", "AUDUSD=X", "fx", "Commodity FX"),
    FeedInstrument("USDCNH", "USD/CNH", "CNH=X", "fx", "China currency pressure"),
    FeedInstrument("XAU", "Gold", "GC=F", "commodities", "Safe-haven / inflation hedge"),
    FeedInstrument("WTI", "Oil WTI", "CL=F", "commodities", "Growth and energy pressure"),
    FeedInstrument("COPPER", "Copper", "HG=F", "commodities", "Industrial cycle proxy"),
    FeedInstrument("SILVER", "Silver", "SI=F", "commodities", "Safe-haven and cyclicality"),
    FeedInstrument("BTC", "Bitcoin", "BTC-USD", "crypto", "Global risk appetite"),
    FeedInstrument("ETH", "Ethereum", "ETH-USD", "crypto", "Crypto breadth"),
)


class GlobalMarketFeedProducer:
    def __init__(self, *, cache_dir: Path = GLOBAL_MARKET_CACHE_DIR, max_cache_age_seconds: int = 300) -> None:
        self.cache_dir = cache_dir
        self.max_cache_age_seconds = max_cache_age_seconds

    def snapshot(self) -> dict[str, Any]:
        cached = self._load_cache()
        if not self._is_cache_fresh(cached):
            live = self._fetch_yahoo_snapshot()
            if live["items"]:
                self._write_cache(live)
                cached = live

        items = cached.get("items", []) if isinstance(cached, dict) else []
        by_group = {"indices": [], "fx": [], "commodities": [], "crypto": []}
        for item in items:
            group = item.get("group")
            if group in by_group:
                by_group[group].append(item)

        return {
            "as_of": cached.get("as_of") if isinstance(cached, dict) else None,
            "source": cached.get("source", "yahoo_finance") if isinstance(cached, dict) else "yahoo_finance",
            "freshness": "fresh" if self._is_cache_fresh(cached) else "stale" if items else "degraded",
            "stale_reason": None if self._is_cache_fresh(cached) else "live_feed_unavailable_using_cache" if items else "live_feed_unavailable_no_cache",
            "groups": by_group,
        }

    def history(self, *, symbol: str, period: str = "6mo", interval: str = "1d") -> dict[str, Any]:
        instrument = find_instrument(symbol)
        if instrument is None:
            return {
                "symbol": symbol.upper(),
                "name": symbol.upper(),
                "points": [],
                "freshness": "degraded",
                "stale_reason": "unknown_symbol",
                "source": "yahoo_finance",
                "as_of": _utc_now_iso(),
            }

        cached = self._load_history_cache(instrument.symbol, period, interval)
        if not self._is_cache_fresh(cached):
            live = self._fetch_yahoo_history(instrument=instrument, period=period, interval=interval)
            if live["points"]:
                self._write_history_cache(instrument.symbol, period, interval, live)
                cached = live

        points = cached.get("points", []) if isinstance(cached, dict) else []
        return {
            "symbol": instrument.symbol,
            "name": instrument.name,
            "yahoo_symbol": instrument.yahoo_symbol,
            "group": instrument.group,
            "focus": instrument.focus,
            "period": period,
            "interval": interval,
            "points": points,
            "source": "yahoo_finance",
            "as_of": cached.get("as_of") if isinstance(cached, dict) else _utc_now_iso(),
            "freshness": "fresh" if self._is_cache_fresh(cached) else "stale" if points else "degraded",
            "stale_reason": None if self._is_cache_fresh(cached) else "history_live_feed_unavailable_using_cache" if points else "history_live_feed_unavailable_no_cache",
        }

    def _fetch_yahoo_snapshot(self) -> dict[str, Any]:
        try:
            import yfinance as yf

            tickers = [instrument.yahoo_symbol for instrument in GLOBAL_MARKET_INSTRUMENTS]
            frame = yf.download(
                tickers=tickers,
                period="5d",
                interval="1d",
                auto_adjust=True,
                progress=False,
                threads=True,
            )
        except Exception:
            return {"as_of": _utc_now_iso(), "source": "yahoo_finance", "items": []}

        items: list[dict[str, Any]] = []
        for instrument in GLOBAL_MARKET_INSTRUMENTS:
            closes = _extract_close_series(frame, instrument.yahoo_symbol)
            if closes.empty:
                continue
            previous = closes.iloc[-2] if len(closes) >= 2 else closes.iloc[-1]
            current = closes.iloc[-1]
            if not previous or pd.isna(previous) or pd.isna(current):
                continue
            change = float(current) - float(previous)
            change_pct = (change / float(previous)) * 100 if float(previous) else 0.0
            items.append(
                {
                    "symbol": instrument.symbol,
                    "name": instrument.name,
                    "yahoo_symbol": instrument.yahoo_symbol,
                    "group": instrument.group,
                    "price": round(float(current), 6),
                    "change": round(change, 6),
                    "change_pct": round(change_pct, 3),
                    "focus": instrument.focus,
                    "source": "yahoo_finance",
                    "updated_at": _series_updated_at(closes),
                }
            )
        return {"as_of": _utc_now_iso(), "source": "yahoo_finance", "items": items}

    def _fetch_yahoo_history(self, *, instrument: FeedInstrument, period: str, interval: str) -> dict[str, Any]:
        safe_period = period if period in {"1mo", "3mo", "6mo", "1y", "2y", "5y"} else "6mo"
        safe_interval = interval if interval in {"1d", "1wk", "1mo"} else "1d"
        try:
            import yfinance as yf

            frame = yf.download(
                tickers=instrument.yahoo_symbol,
                period=safe_period,
                interval=safe_interval,
                auto_adjust=True,
                progress=False,
                threads=False,
            )
        except Exception:
            return {"as_of": _utc_now_iso(), "source": "yahoo_finance", "points": []}

        closes = _extract_close_series(frame, instrument.yahoo_symbol)
        points: list[dict[str, Any]] = []
        previous: float | None = None
        for index, value in closes.tail(260).items():
            if pd.isna(value):
                continue
            price = float(value)
            change_pct = ((price - previous) / previous) * 100 if previous else 0.0
            previous = price
            points.append(
                {
                    "date": _timestamp_iso(index),
                    "price": round(price, 6),
                    "change_pct": round(change_pct, 4),
                }
            )
        return {"as_of": _utc_now_iso(), "source": "yahoo_finance", "points": points}

    def _load_cache(self) -> dict[str, Any]:
        path = self.cache_dir / "global_market_snapshot.json"
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _load_history_cache(self, symbol: str, period: str, interval: str) -> dict[str, Any]:
        path = self.cache_dir / "history" / f"{symbol}_{period}_{interval}.json"
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _write_cache(self, payload: dict[str, Any]) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path = self.cache_dir / "global_market_snapshot.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def _write_history_cache(self, symbol: str, period: str, interval: str, payload: dict[str, Any]) -> None:
        path = self.cache_dir / "history" / f"{symbol}_{period}_{interval}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def _is_cache_fresh(self, payload: dict[str, Any] | None) -> bool:
        if not payload or not payload.get("as_of"):
            return False
        try:
            as_of = datetime.fromisoformat(str(payload["as_of"]).replace("Z", "+00:00"))
        except ValueError:
            return False
        return datetime.now(timezone.utc) - as_of <= timedelta(seconds=self.max_cache_age_seconds)


def _extract_close_series(frame: pd.DataFrame, yahoo_symbol: str) -> pd.Series:
    if frame is None or frame.empty:
        return pd.Series(dtype=float)
    try:
        if isinstance(frame.columns, pd.MultiIndex):
            if ("Close", yahoo_symbol) in frame.columns:
                series = frame[("Close", yahoo_symbol)]
            elif (yahoo_symbol, "Close") in frame.columns:
                series = frame[(yahoo_symbol, "Close")]
            else:
                return pd.Series(dtype=float)
        elif "Close" in frame.columns:
            series = frame["Close"]
        else:
            return pd.Series(dtype=float)
        return pd.to_numeric(series, errors="coerce").dropna()
    except Exception:
        return pd.Series(dtype=float)


def _series_updated_at(series: pd.Series) -> str:
    try:
        ts = pd.Timestamp(series.index[-1])
        if ts.tzinfo is None:
            ts = ts.tz_localize(timezone.utc)
        else:
            ts = ts.tz_convert(timezone.utc)
        return ts.isoformat()
    except Exception:
        return _utc_now_iso()


def find_instrument(symbol: str) -> FeedInstrument | None:
    normalized = symbol.strip().upper()
    return next((instrument for instrument in GLOBAL_MARKET_INSTRUMENTS if instrument.symbol == normalized or instrument.yahoo_symbol.upper() == normalized), None)


def _timestamp_iso(value) -> str:
    try:
        ts = pd.Timestamp(value)
        if ts.tzinfo is None:
            ts = ts.tz_localize(timezone.utc)
        else:
            ts = ts.tz_convert(timezone.utc)
        return ts.isoformat()
    except Exception:
        return _utc_now_iso()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
