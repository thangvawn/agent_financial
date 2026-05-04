"""Tests cho cache OHLCV watchlist (không cần mạng khi mock)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from risk_dashboard.data.watchlist_prices import (
    _normalize_hist_df,
    ohlcv_to_bars_json,
    parse_ticker_list,
    sync_watchlist_ticker,
)


def test_parse_ticker_list():
    assert parse_ticker_list(["fpt", " VIC "]) == ["FPT", "VIC"]


def test_normalize_hist_df():
    idx = pd.date_range("2024-01-02", periods=5, freq="B")
    raw = pd.DataFrame(
        {
            "Open": np.linspace(10, 11, 5),
            "High": np.linspace(11, 12, 5),
            "Low": np.linspace(9, 10, 5),
            "Close": np.linspace(10.5, 11.5, 5),
            "Volume": np.linspace(1e6, 2e6, 5),
        },
        index=idx,
    )
    out = _normalize_hist_df(raw)
    assert len(out) == 5
    assert list(out.columns) == ["open", "high", "low", "close", "volume"]


def test_ohlcv_to_bars_json():
    idx = pd.date_range("2024-01-02", periods=3, freq="B")
    df = pd.DataFrame(
        {
            "open": [1, 2, 3],
            "high": [2, 3, 4],
            "low": [0.5, 1.5, 2.5],
            "close": [1.5, 2.5, 3.5],
            "volume": [100, 200, 300],
        },
        index=idx,
    )
    bars = ohlcv_to_bars_json(df)
    assert len(bars) == 3
    assert set(bars[0].keys()) == {"time", "open", "high", "low", "close", "volume"}


def test_sync_merges_new_rows(monkeypatch, tmp_path):
    from risk_dashboard.data import watchlist_prices as m

    monkeypatch.setattr(m, "WATCHLIST_PRICE_DIR", tmp_path)

    d1 = pd.Timestamp("2023-06-01")
    pd.DataFrame(
        {
            "open": [10.0],
            "high": [11.0],
            "low": [9.0],
            "close": [10.5],
            "volume": [1e6],
        },
        index=[d1],
    ).to_parquet(tmp_path / "FPT.parquet")

    d2 = pd.Timestamp("2023-06-15")

    def fake_download(sym: str, start: date, end: date) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "open": [11.0],
                "high": [12.0],
                "low": [10.0],
                "close": [11.5],
                "volume": [1.2e6],
            },
            index=[d2],
        )

    monkeypatch.setattr(m, "_download_yf_range", fake_download)

    out = sync_watchlist_ticker("FPT")
    assert len(out) == 2
    assert out.index.max() == d2.normalize()
