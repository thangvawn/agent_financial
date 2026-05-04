from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
CROSS_ASSET_PRICE_DIR = _PROJECT_ROOT / "data" / "cross_asset_prices"
_DEFAULT_HISTORY_DAYS = 365 * 3


@dataclass(frozen=True)
class CrossAssetDefinition:
    id: str
    label: str
    symbol: str
    market: str
    focus: str


CROSS_ASSET_PRESETS: tuple[CrossAssetDefinition, ...] = (
    CrossAssetDefinition(
        id="gold",
        label="Vàng",
        symbol="GC=F",
        market="commodity",
        focus="Trú ẩn và kỳ vọng lạm phát",
    ),
    CrossAssetDefinition(
        id="silver",
        label="Bạc",
        symbol="SI=F",
        market="commodity",
        focus="Cân bằng giữa trú ẩn và nhạy chu kỳ",
    ),
    CrossAssetDefinition(
        id="bitcoin",
        label="BTC",
        symbol="BTC-USD",
        market="crypto",
        focus="Khẩu vị rủi ro và beta toàn cầu",
    ),
    CrossAssetDefinition(
        id="ethereum",
        label="ETH",
        symbol="ETH-USD",
        market="crypto",
        focus="Độ rộng risk-on trong crypto",
    ),
)


def _cache_key(raw: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", raw.strip().upper()).strip("_")


def _normalize_hist_df(hist: pd.DataFrame) -> pd.DataFrame:
    if hist is None or hist.empty:
        return pd.DataFrame()

    df = hist.rename(columns=lambda c: str(c).lower())
    if "close" not in df.columns:
        return pd.DataFrame()

    keep_cols = [c for c in ("open", "high", "low", "close", "volume") if c in df.columns]
    out = df[keep_cols].copy()
    idx = pd.to_datetime(out.index)
    if hasattr(idx, "tz") and idx.tz is not None:
        idx = idx.tz_localize(None)
    out.index = idx.normalize()
    out = out[~out.index.duplicated(keep="last")]
    out = out.sort_index()
    for c in keep_cols:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    return out.dropna(subset=["close"])


def _download_yf_range(symbol: str, start: date, end: date) -> pd.DataFrame:
    import yfinance as yf

    end_adj = end + timedelta(days=1)
    hist = yf.Ticker(symbol).history(start=start, end=end_adj, auto_adjust=True)
    return _normalize_hist_df(hist)


def _cache_path(asset: CrossAssetDefinition) -> Path:
    return CROSS_ASSET_PRICE_DIR / f"{asset.id}_{_cache_key(asset.symbol)}.parquet"


def load_cached_ohlcv(asset: CrossAssetDefinition) -> pd.DataFrame | None:
    path = _cache_path(asset)
    if not path.exists():
        return None
    try:
        df = pd.read_parquet(path)
        df.index = pd.to_datetime(df.index)
        return df.sort_index()
    except Exception as exc:
        logger.warning("Đọc cache cross-asset %s lỗi, tải lại: %s", path, exc)
        return None


def sync_cross_asset_history(
    asset: CrossAssetDefinition,
    *,
    max_history_days: int = _DEFAULT_HISTORY_DAYS,
) -> pd.DataFrame:
    CROSS_ASSET_PRICE_DIR.mkdir(parents=True, exist_ok=True)
    # Yahoo often has no complete daily bar for futures on the current calendar
    # day yet. Fetching today -> tomorrow creates noisy "possibly delisted"
    # errors for GC=F/SI=F, so use the last completed daily bar for this legacy
    # cross-asset endpoint.
    end = date.today() - timedelta(days=1)
    path = _cache_path(asset)

    cached = load_cached_ohlcv(asset)
    if cached is not None and not cached.empty:
        last_d = cached.index.max().date()
        start_fetch = last_d + timedelta(days=1)
        if start_fetch > end:
            return cached
        new = _download_yf_range(asset.symbol, start_fetch, end)
        if new.empty:
            return cached
        merged = pd.concat([cached, new])
    else:
        start = end - timedelta(days=max_history_days)
        merged = _download_yf_range(asset.symbol, start, end)
        if merged.empty:
            raise ValueError(f"Không tải được dữ liệu cho {asset.label} ({asset.symbol}).")

    merged = merged[~merged.index.duplicated(keep="last")]
    merged = merged.sort_index()
    try:
        merged.to_parquet(path)
    except Exception as exc:
        logger.warning("Ghi parquet %s: %s", path, exc)
    return merged


def _pct_change(df: pd.DataFrame, sessions: int) -> float | None:
    if len(df) <= sessions:
        return None
    curr = float(df["close"].iloc[-1])
    prev = float(df["close"].iloc[-(sessions + 1)])
    if prev == 0:
        return None
    return (curr / prev - 1.0) * 100.0


def _decision_hint(asset: CrossAssetDefinition, *, change_1w: float | None, change_1m: float | None) -> str:
    if asset.market == "commodity":
        if (change_1w or 0) >= 2 or (change_1m or 0) >= 5:
            return "Tài sản trú ẩn tăng, nên kiểm tra xem tâm lý risk-off có đang mạnh lên không."
        if (change_1w or 0) <= -2 and (change_1m or 0) <= -3:
            return "Nhóm trú ẩn đang hạ nhiệt, áp lực phòng thủ có thể bớt căng."
        return "Dùng như bộ lọc trú ẩn trước khi tăng beta danh mục."

    if (change_1w or 0) >= 5 or (change_1m or 0) >= 12:
        return "Crypto đang mở rộng beta, khẩu vị rủi ro toàn cầu có dấu hiệu nới ra."
    if (change_1w or 0) <= -5 or (change_1m or 0) <= -12:
        return "Crypto suy yếu rõ, nên thận trọng với các quyết định thiên về risk-on."
    return "Theo dõi để đọc nhanh nhiệt độ risk-on/risk-off ngoài thị trường Việt Nam."


def _line_points(df: pd.DataFrame) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for idx, close in df["close"].items():
        ts = pd.Timestamp(idx)
        if ts.tzinfo is not None:
            ts = ts.tz_localize(None)
        out.append(
            {
                "time": int(ts.replace(hour=12, minute=0, second=0).timestamp()),
                "value": round(float(close), 6),
            }
        )
    return out


def build_cross_asset_dashboard(limit: int = 180) -> dict[str, Any]:
    safe_limit = max(30, min(int(limit), 365))
    assets_payload: list[dict[str, Any]] = []

    for asset in CROSS_ASSET_PRESETS:
        try:
            df = sync_cross_asset_history(asset)
            tail = df.tail(safe_limit)
            latest_ts = tail.index.max() if not tail.empty else None
            change_1w = _pct_change(df, 5)
            change_1m = _pct_change(df, 21)
            assets_payload.append(
                {
                    "id": asset.id,
                    "label": asset.label,
                    "symbol": asset.symbol,
                    "market": asset.market,
                    "focus": asset.focus,
                    "status": "ok",
                    "currency": "USD",
                    "price": round(float(df["close"].iloc[-1]), 6),
                    "change_1d_pct": _pct_change(df, 1),
                    "change_1w_pct": change_1w,
                    "change_1m_pct": change_1m,
                    "bars": _line_points(tail),
                    "source": "yfinance + cache (data/cross_asset_prices)",
                    "updated_at": latest_ts.date().isoformat() if latest_ts is not None else None,
                    "decision_hint": _decision_hint(asset, change_1w=change_1w, change_1m=change_1m),
                }
            )
        except Exception as exc:
            logger.info("Cross-asset %s failed: %s", asset.symbol, exc)
            assets_payload.append(
                {
                    "id": asset.id,
                    "label": asset.label,
                    "symbol": asset.symbol,
                    "market": asset.market,
                    "focus": asset.focus,
                    "status": "error",
                    "bars": [],
                    "error": str(exc),
                }
            )

    return {
        "as_of": date.today().isoformat(),
        "assets": assets_payload,
    }
