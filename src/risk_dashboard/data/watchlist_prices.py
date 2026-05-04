"""
Cache OHLCV cổ phiếu VN cho vùng theo dõi (watchlist): lưu parquet, bổ sung dữ liệu mới qua yfinance.
"""
from __future__ import annotations

import logging
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
WATCHLIST_PRICE_DIR = _PROJECT_ROOT / "data" / "watchlist_prices"
_DEFAULT_HISTORY_DAYS = 365 * 5


def _clean_ticker(raw: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", raw.strip()).upper()


def parse_ticker_list(tickers: list[str]) -> list[str]:
    out: list[str] = []
    for x in tickers:
        t = _clean_ticker(x)
        if t and t not in out:
            out.append(t)
    if not out:
        raise ValueError("Cần ít nhất một mã hợp lệ.")
    if len(out) > 40:
        raise ValueError("Tối đa 40 mã mỗi lần đồng bộ.")
    return out


def _yf_symbol(ticker: str) -> str:
    return f"{ticker.upper()}.VN"


def _normalize_hist_df(hist: pd.DataFrame) -> pd.DataFrame:
    """Chuẩn hóa DataFrame từ Ticker.history() — cột open..volume, index ngày."""
    if hist is None or hist.empty:
        return pd.DataFrame()

    df = hist.rename(columns=lambda c: str(c).lower())
    for c in ("open", "high", "low", "close", "volume"):
        if c not in df.columns:
            return pd.DataFrame()

    out = df[["open", "high", "low", "close", "volume"]].copy()
    idx = pd.to_datetime(out.index)
    if hasattr(idx, "tz") and idx.tz is not None:
        idx = idx.tz_localize(None)
    out.index = idx.normalize()
    out = out[~out.index.duplicated(keep="last")]
    out = out.sort_index()
    for c in ("open", "high", "low", "close", "volume"):
        out[c] = pd.to_numeric(out[c], errors="coerce")
    return out.dropna(how="any")


def _download_yf_range(symbol: str, start: date, end: date) -> pd.DataFrame:
    import yfinance as yf

    end_adj = end + timedelta(days=1)
    hist = yf.Ticker(symbol).history(start=start, end=end_adj, auto_adjust=True)
    return _normalize_hist_df(hist)


def _cache_path(ticker: str) -> Path:
    return WATCHLIST_PRICE_DIR / f"{_clean_ticker(ticker)}.parquet"


def load_cached_ohlcv(ticker: str) -> pd.DataFrame | None:
    path = _cache_path(ticker)
    if not path.exists():
        return None
    try:
        df = pd.read_parquet(path)
        df.index = pd.to_datetime(df.index)
        return df.sort_index()
    except Exception as exc:
        logger.warning("Đọc cache OHLCV %s lỗi, tải lại: %s", path, exc)
        return None


def sync_watchlist_ticker(ticker: str, *, max_history_days: int = _DEFAULT_HISTORY_DAYS) -> pd.DataFrame:
    """
    Bổ sung dữ liệu giá/khối lượng cho một mã: đọc parquet nếu có, tải phần còn thiếu từ yfinance, ghi lại cache.
    """
    t = _clean_ticker(ticker)
    sym = _yf_symbol(t)
    WATCHLIST_PRICE_DIR.mkdir(parents=True, exist_ok=True)
    path = _cache_path(t)
    end = date.today()

    cached = load_cached_ohlcv(t)
    if cached is not None and not cached.empty:
        last_d = cached.index.max().date()
        start_fetch = last_d + timedelta(days=1)
        if start_fetch > end:
            return cached
        new = _download_yf_range(sym, start_fetch, end)
        if new.empty:
            return cached
        merged = pd.concat([cached, new])
    else:
        start = end - timedelta(days=max_history_days)
        merged = _download_yf_range(sym, start, end)
        if merged.empty:
            raise ValueError(f"Không tải được OHLCV cho {t} ({sym}). Kiểm tra mã hoặc mạng.")

    merged = merged[~merged.index.duplicated(keep="last")]
    merged = merged.sort_index()
    try:
        merged.to_parquet(path)
    except Exception as exc:
        logger.warning("Ghi parquet %s: %s", path, exc)

    return merged


def sync_watchlist_tickers(tickers: list[str]) -> dict[str, Any]:
    """Đồng bộ nhiều mã; trả về số dòng và lỗi từng mã."""
    parsed = parse_ticker_list(tickers)
    details: dict[str, dict[str, Any]] = {}
    errors: dict[str, str] = {}
    for t in parsed:
        try:
            df = sync_watchlist_ticker(t)
            details[t] = {"rows": int(len(df)), "from": str(df.index.min().date()), "to": str(df.index.max().date())}
        except Exception as exc:
            errors[t] = str(exc)
            logger.info("sync_watchlist_ticker %s: %s", t, exc)
    return {"synced": list(details.keys()), "details": details, "errors": errors}


def ohlcv_to_bars_json(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Chuyển DataFrame sang mảng nến cho lightweight-charts."""
    out: list[dict[str, Any]] = []
    for idx, row in df.iterrows():
        ts = pd.Timestamp(idx)
        if ts.tzinfo is not None:
            ts = ts.tz_localize(None)
        tsec = int(ts.replace(hour=12, minute=0, second=0).timestamp())
        out.append(
            {
                "time": tsec,
                "open": round(float(row["open"]), 4),
                "high": round(float(row["high"]), 4),
                "low": round(float(row["low"]), 4),
                "close": round(float(row["close"]), 4),
                "volume": float(row["volume"]),
            }
        )
    return out
