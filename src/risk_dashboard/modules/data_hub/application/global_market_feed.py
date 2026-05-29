from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import contextlib
import json
from pathlib import Path
from typing import Any

import pandas as pd


_PROJECT_ROOT = Path(__file__).resolve().parents[5]
GLOBAL_MARKET_CACHE_DIR = _PROJECT_ROOT / "data" / "global_market_prices"
_SUPPORTED_HISTORY_INTERVALS = {"1m", "5m", "15m", "30m", "1h", "4h", "1d", "1wk", "1mo", "1y"}


@dataclass(frozen=True)
class FeedInstrument:
    symbol: str
    name: str
    yahoo_symbol: str
    group: str
    focus: str
    data_source: str = "yahoo"  # "yahoo" or "vnstock"
    vn_symbol: str = ""  # only used when data_source == "vnstock"


GLOBAL_MARKET_INSTRUMENTS: tuple[FeedInstrument, ...] = (
    FeedInstrument("VNINDEX", "VN-Index", "", "indices", "Vietnam broad market", data_source="vnstock", vn_symbol="VNINDEX"),
    FeedInstrument("VN30", "VN30", "", "indices", "Vietnam large-cap", data_source="vnstock", vn_symbol="VN30"),
    FeedInstrument("HNXINDEX", "HNX-Index", "", "indices", "Vietnam HNX board", data_source="vnstock", vn_symbol="HNXIndex"),
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
            if instrument.data_source == "vnstock":
                live = self._fetch_vnstock_history(instrument=instrument, period=period, interval=interval)
            else:
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
            "source": instrument.data_source if instrument.data_source != "yahoo" else "yahoo_finance",
            "as_of": cached.get("as_of") if isinstance(cached, dict) else _utc_now_iso(),
            "freshness": "fresh" if self._is_cache_fresh(cached) else "stale" if points else "degraded",
            "stale_reason": None if self._is_cache_fresh(cached) else "history_live_feed_unavailable_using_cache" if points else "history_live_feed_unavailable_no_cache",
        }

    def _fetch_yahoo_snapshot(self) -> dict[str, Any]:
        yahoo_instruments = [i for i in GLOBAL_MARKET_INSTRUMENTS if i.data_source == "yahoo"]
        try:
            import yfinance as yf

            tickers = [instrument.yahoo_symbol for instrument in yahoo_instruments]
            frame = yf.download(
                tickers=tickers,
                period="5d",
                interval="1d",
                auto_adjust=True,
                progress=False,
                threads=True,
            )
        except Exception:
            frame = pd.DataFrame()

        items: list[dict[str, Any]] = []
        for instrument in yahoo_instruments:
            closes = _extract_close_series(frame, instrument.yahoo_symbol) if not frame.empty else pd.Series(dtype=float)
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
        items.extend(self._fetch_vnstock_snapshot_items())
        return {"as_of": _utc_now_iso(), "source": "mixed", "items": items}

    def _fetch_vnstock_snapshot_items(self) -> list[dict[str, Any]]:
        vn_instruments = [i for i in GLOBAL_MARKET_INSTRUMENTS if i.data_source == "vnstock"]
        if not vn_instruments:
            return []
        items: list[dict[str, Any]] = []
        for instrument in vn_instruments:
            frame = _fetch_vnstock_dataframe(instrument.vn_symbol or instrument.symbol, days=5, interval="1D")
            if frame is None or frame.empty or "close" not in frame.columns:
                continue
            closes = pd.to_numeric(frame["close"], errors="coerce").dropna()
            if closes.empty:
                continue
            previous = float(closes.iloc[-2]) if len(closes) >= 2 else float(closes.iloc[-1])
            current = float(closes.iloc[-1])
            change = current - previous
            change_pct = (change / previous) * 100 if previous else 0.0
            items.append(
                {
                    "symbol": instrument.symbol,
                    "name": instrument.name,
                    "yahoo_symbol": instrument.vn_symbol,
                    "group": instrument.group,
                    "price": round(current, 6),
                    "change": round(change, 6),
                    "change_pct": round(change_pct, 3),
                    "focus": instrument.focus,
                    "source": "vnstock",
                    "updated_at": _utc_now_iso(),
                }
            )
        return items

    def _fetch_yahoo_history(self, *, instrument: FeedInstrument, period: str, interval: str) -> dict[str, Any]:
        safe_period = _normalize_history_period(period, interval)
        safe_interval = _download_interval_for_history(interval)
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

        normalized = _extract_ohlcv_frame(frame, instrument.yahoo_symbol)
        normalized = _resample_history_frame(normalized, interval)
        closes = normalized["close"] if not normalized.empty and "close" in normalized.columns else pd.Series(dtype=float)
        points: list[dict[str, Any]] = []
        previous: float | None = None
        for index, row in normalized.tail(_history_point_limit(interval)).iterrows():
            value = row.get("close")
            if pd.isna(value):
                continue
            price = float(value)
            change_pct = ((price - previous) / previous) * 100 if previous else 0.0
            previous = price
            points.append(
                {
                    "date": _timestamp_iso(index),
                    "price": round(price, 6),
                    "open": round(float(row.get("open", price)), 6),
                    "high": round(float(row.get("high", price)), 6),
                    "low": round(float(row.get("low", price)), 6),
                    "close": round(price, 6),
                    "volume": round(float(row.get("volume", 0.0)), 4),
                    "change_pct": round(change_pct, 4),
                }
            )
        return {"as_of": _utc_now_iso(), "source": "yahoo_finance", "points": points}

    def _fetch_vnstock_history(self, *, instrument: FeedInstrument, period: str, interval: str) -> dict[str, Any]:
        days = _period_to_days(period)
        vn_interval = _vnstock_interval(interval)
        vn_symbol = instrument.vn_symbol or instrument.symbol
        frame = _fetch_vnstock_dataframe(vn_symbol, days=days, interval=vn_interval)
        if frame is None or frame.empty:
            return {"as_of": _utc_now_iso(), "source": "vnstock", "points": []}

        # vnstock returns VN equity prices in thousands of VND (e.g. 75.1 = 75,100 VND).
        # Multiply to raw VND so chart axes / OHLC strip stay aligned with snapshot.
        # Indices (VNINDEX/VN30/HNXINDEX) are quoted in index points — don't scale.
        scale = 1000.0 if _is_vn_stock_equity(instrument) else 1.0

        points: list[dict[str, Any]] = []
        previous: float | None = None
        date_col = "time" if "time" in frame.columns else frame.columns[0]
        limit = _history_point_limit(interval)
        for _, row in frame.tail(limit).iterrows():
            close_val = row.get("close")
            if close_val is None or (isinstance(close_val, float) and pd.isna(close_val)):
                continue
            price = float(close_val) * scale
            change_pct = ((price - previous) / previous) * 100 if previous else 0.0
            previous = price
            points.append(
                {
                    "date": _timestamp_iso(row.get(date_col)),
                    "price": round(price, 6),
                    "open": round(float(row.get("open", close_val) or close_val) * scale, 6),
                    "high": round(float(row.get("high", close_val) or close_val) * scale, 6),
                    "low": round(float(row.get("low", close_val) or close_val) * scale, 6),
                    "close": round(price, 6),
                    "volume": round(float(row.get("volume", 0.0) or 0.0), 4),
                    "change_pct": round(change_pct, 4),
                }
            )
        return {"as_of": _utc_now_iso(), "source": "vnstock", "points": points}

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


def _extract_field_series(frame: pd.DataFrame, yahoo_symbol: str, field: str) -> pd.Series:
    if frame is None or frame.empty:
        return pd.Series(dtype=float)
    try:
        if isinstance(frame.columns, pd.MultiIndex):
            if (field, yahoo_symbol) in frame.columns:
                series = frame[(field, yahoo_symbol)]
            elif (yahoo_symbol, field) in frame.columns:
                series = frame[(yahoo_symbol, field)]
            else:
                return pd.Series(dtype=float)
        elif field in frame.columns:
            series = frame[field]
        else:
            return pd.Series(dtype=float)
        series = pd.to_numeric(series, errors="coerce")
        series.index = pd.to_datetime(series.index)
        if hasattr(series.index, "tz") and series.index.tz is not None:
            series.index = series.index.tz_localize(None)
        return series.dropna().sort_index()
    except Exception:
        return pd.Series(dtype=float)


def _extract_ohlcv_frame(frame: pd.DataFrame, yahoo_symbol: str) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    data = {}
    for field in ("Open", "High", "Low", "Close", "Volume"):
        series = _extract_field_series(frame, yahoo_symbol, field)
        if series.empty and field != "Volume":
            return pd.DataFrame()
        data[field.lower()] = series
    out = pd.DataFrame(data).dropna(subset=["open", "high", "low", "close"]).sort_index()
    out = out[~out.index.duplicated(keep="last")]
    return out


def _normalize_history_period(period: str, interval: str) -> str:
    safe_period = period if period in {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"} else "6mo"
    if interval == "1m" and safe_period not in {"1d", "5d"}:
        return "5d"
    if interval in {"5m", "15m", "30m"} and safe_period not in {"1d", "5d", "1mo"}:
        return "1mo"
    if interval in {"1h", "4h"} and safe_period not in {"5d", "1mo", "3mo", "6mo", "1y"}:
        return "1y"
    if interval == "1y" and safe_period in {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y"}:
        return "5y"
    return safe_period


_PERIOD_TO_DAYS = {
    "1d": 5,      # account for weekends so we always land on at least 1 trading day
    "5d": 10,
    "1mo": 35,
    "3mo": 100,
    "6mo": 200,
    "1y": 380,
    "2y": 760,
    "5y": 1900,
    "10y": 3800,
    "max": 9000,  # vnstock historical depth ~ 2000-01-01
}


def _period_to_days(period: str) -> int:
    return _PERIOD_TO_DAYS.get(period, 200)


_VNSTOCK_INTERVAL_MAP = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1H",
    "4h": "1H",   # vnstock has no native 4h for indices — caller may resample
    "1d": "1D",
    "1wk": "1W",
    "1mo": "1M",
    "1y": "1M",   # vnstock has no yearly bucket — fall back to monthly
}


def _vnstock_interval(interval: str) -> str:
    return _VNSTOCK_INTERVAL_MAP.get(interval, "1D")


def _fetch_vnstock_dataframe(symbol: str, *, days: int, interval: str) -> pd.DataFrame | None:
    """Fetch VN OHLCV from vnstock.

    VN equities are only served by the VCI source in vnstock 4.x.
    The MSN/KBS providers are international and have no VN coverage,
    so we don't waste retry budget on them. The internal vnstock retry
    decorator handles transient transport failures on VCI.

    Wrapped in a rate-limiter (15 req/min, well under vnstock guest 20/min)
    and a SystemExit shield so vnstock's "Process terminated" on rate-limit
    does not crash the uvicorn worker.
    """
    from datetime import date, timedelta

    end = date.today()
    start = end - timedelta(days=max(days, 5))
    start_s = start.isoformat()
    end_s = end.isoformat()

    _VNSTOCK_RATE_LIMITER.acquire()
    try:
        with _vnstock_safe():
            try:
                from vnstock import Quote  # type: ignore

                q = Quote(symbol=symbol, source="VCI")
                frame = q.history(start=start_s, end=end_s, interval=interval)
                if isinstance(frame, pd.DataFrame) and not frame.empty:
                    return frame
            except Exception:
                pass

            try:
                from vnstock import Vnstock  # type: ignore

                stock = Vnstock().stock(symbol=symbol, source="VCI")
                frame = stock.quote.history(start=start_s, end=end_s, interval=interval)
                if isinstance(frame, pd.DataFrame) and not frame.empty:
                    return frame
            except Exception:
                pass
    except _VnstockRateExceeded:
        return None

    return None


class _VnstockRateExceeded(RuntimeError):
    """Raised when vnstock library tries to terminate the process on rate limit."""


@contextlib.contextmanager
def _vnstock_safe():
    """Intercept vnstock's sys.exit()/os._exit() rate-limit kill so we degrade gracefully."""
    import os as _os
    import sys as _sys

    original_sys_exit = _sys.exit
    original_os_exit = _os._exit

    def _trap(code=0):
        raise _VnstockRateExceeded(f"vnstock attempted to terminate process (code={code})")

    _sys.exit = _trap
    _os._exit = _trap
    try:
        yield
    finally:
        _sys.exit = original_sys_exit
        _os._exit = original_os_exit


class _RateLimiter:
    """Sliding-window rate limiter. Blocks until under max_requests in window_seconds."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        import threading as _t

        self.max_requests = max_requests
        self.window = window_seconds
        self._lock = _t.Lock()
        self._timestamps: list[float] = []

    def acquire(self) -> None:
        import time as _time

        while True:
            with self._lock:
                now = _time.time()
                # Drop timestamps outside the window
                cutoff = now - self.window
                while self._timestamps and self._timestamps[0] < cutoff:
                    self._timestamps.pop(0)
                if len(self._timestamps) < self.max_requests:
                    self._timestamps.append(now)
                    return
                wait_for = max(0.0, (self._timestamps[0] + self.window) - now)
            _time.sleep(min(wait_for + 0.05, 2.0))


# Global rate limiter — vnstock guest tier allows 20 req/min, we cap at 15/min for safety.
_VNSTOCK_RATE_LIMITER = _RateLimiter(max_requests=15, window_seconds=60)


def _download_interval_for_history(interval: str) -> str:
    normalized = interval if interval in _SUPPORTED_HISTORY_INTERVALS else "1d"
    if normalized in {"1h", "4h"}:
        return "60m"
    if normalized == "1y":
        return "1mo"
    return normalized


def _resample_history_frame(frame: pd.DataFrame, interval: str) -> pd.DataFrame:
    if frame.empty:
        return frame
    if interval == "4h":
        return (
            frame.resample("4h")
            .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
            .dropna(subset=["open", "high", "low", "close"])
        )
    if interval == "1y":
        return (
            frame.resample("YE")
            .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
            .dropna(subset=["open", "high", "low", "close"])
        )
    return frame


def _history_point_limit(interval: str) -> int:
    if interval in {"1m", "5m", "15m", "30m"}:
        return 1200
    if interval in {"1h", "4h"}:
        return 600
    if interval in {"1wk", "1mo", "1y"}:
        return 520
    return 800


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
    hit = next(
        (instrument for instrument in GLOBAL_MARKET_INSTRUMENTS
         if instrument.symbol == normalized or instrument.yahoo_symbol.upper() == normalized),
        None,
    )
    if hit is not None:
        return hit
    # Fall through: arbitrary VN ticker (3-5 letters) routed to vnstock.
    if _looks_like_vn_ticker(normalized):
        return FeedInstrument(
            symbol=normalized,
            name=normalized,
            yahoo_symbol="",
            group="vn_stocks",
            focus="Vietnam equity",
            data_source="vnstock",
            vn_symbol=normalized,
        )
    return None


def _looks_like_vn_ticker(symbol: str) -> bool:
    if not symbol:
        return False
    if not (3 <= len(symbol) <= 5):
        return False
    return symbol.isalpha()


_VN_INDICES = frozenset({"VNINDEX", "VN30", "HNXINDEX", "HNXINDEX30", "UPCOMINDEX"})


def _is_vn_stock_equity(instrument: FeedInstrument) -> bool:
    """True only for individual VN listings (need ×1000 to raw VND scaling).

    VN indices stay in their natural index-point unit (VN-Index ~1877).
    Synthetic fallthrough instruments use group=vn_stocks → stock.
    """
    if instrument.data_source != "vnstock":
        return False
    sym = (instrument.symbol or "").upper()
    if sym in _VN_INDICES:
        return False
    return True


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
