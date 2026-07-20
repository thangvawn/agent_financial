"""Tests for portfolio backtest (pure math + validation, no network)."""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from risk_dashboard.engines.quant.backtest import (
    backtest_volume_btc_stoploss_strategy,
    compute_buy_and_hold,
    normalize_weights,
    parse_ticker_list,
    validate_date_range,
)


def test_parse_ticker_list_strips_and_dedupes():
    assert parse_ticker_list([" fpt ", "FPT", "vic"]) == ["FPT", "VIC"]


def test_parse_ticker_list_rejects_empty():
    with pytest.raises(ValueError, match="ít nhất"):
        parse_ticker_list(["  ", ""])


def test_normalize_equal_weight():
    w = normalize_weights(["A", "B"], equal_weight=True, weights=None)
    assert w == {"A": 0.5, "B": 0.5}


def test_normalize_explicit_weights():
    w = normalize_weights(["A", "B"], equal_weight=False, weights={"a": 1, "b": 3})
    assert pytest.approx(w["A"], rel=1e-6) == 0.25
    assert pytest.approx(w["B"], rel=1e-6) == 0.75


def test_validate_date_range():
    with pytest.raises(ValueError):
        validate_date_range(date(2024, 1, 10), date(2024, 1, 1))


def test_compute_buy_and_hold_upward_trend():
    idx = pd.date_range("2023-01-01", periods=80, freq="B")
    close = pd.DataFrame(
        {
            "A": np.linspace(100, 110, 80),
            "B": np.linspace(50, 52, 80),
        },
        index=idx,
    )
    out = compute_buy_and_hold(close, {"A": 0.5, "B": 0.5}, 1_000_000.0)
    assert out["metrics"]["total_return_pct"] > 0
    assert out["metrics"]["trading_days"] == 79
    assert len(out["series"]["portfolio"]) >= 79
    assert "drawdown_pct" in out["series"]
    assert isinstance(out["monthly_returns"], list)
    assert isinstance(out["ath_segments"], list)


def test_compute_buy_and_hold_with_benchmark():
    idx = pd.date_range("2023-01-01", periods=80, freq="B")
    close = pd.DataFrame({"A": np.linspace(100, 105, 80), "B": np.linspace(40, 41, 80)}, index=idx)
    bench = pd.Series(np.linspace(1000, 1020, 80), index=idx)
    out = compute_buy_and_hold(close, {"A": 0.5, "B": 0.5}, 2_000_000.0, benchmark_close=bench)
    assert out["series"]["benchmark"] is not None
    assert len(out["series"]["benchmark"]) == len(out["series"]["portfolio"])
    assert out["metrics"]["beta_vs_benchmark"] is not None
    assert out["metrics"]["var_95_daily_pct"] is not None
    assert len(out["series"]["rolling_vol_annual_pct"]) >= 1


def test_compute_buy_and_hold_phase1_metrics_no_benchmark():
    idx = pd.date_range("2023-01-01", periods=80, freq="B")
    close = pd.DataFrame(
        {
            "A": np.linspace(100, 110, 80),
            "B": np.linspace(50, 52, 80),
        },
        index=idx,
    )
    out = compute_buy_and_hold(close, {"A": 0.5, "B": 0.5}, 1_000_000.0)
    assert out["metrics"]["risk_free_annual_pct"] == 4.5
    assert out["metrics"]["alpha_annual_pct_jensen"] is None
    assert out["metrics"]["beta_vs_benchmark"] is None
    assert out["metrics"]["concentration_herfindahl"] == pytest.approx(0.5)


def test_volume_btc_stoploss_strategy_hits_stop_loss():
    idx = pd.date_range("2024-01-01", periods=6, freq="B")
    stock = pd.DataFrame(
        {
            "open": [100, 100, 100, 100, 99, 99],
            "high": [101, 102, 101, 101, 100, 100],
            "low": [99, 99, 99, 95, 98, 98],
            "close": [100, 101, 100, 96, 99, 100],
            "volume": [100, 250, 150, 120, 110, 100],
        },
        index=idx,
    )
    btc = pd.Series([100, 105, 105, 104, 104, 104], index=idx)

    out = backtest_volume_btc_stoploss_strategy(
        {"AAA": stock},
        {"AAA": 1.0},
        1_000_000.0,
        btc_close=btc,
        benchmark_close=None,
        config={
            "volume_spike_multiplier": 2.0,
            "btc_daily_change_min_pct": 3.0,
            "stop_loss_pct": 4.0,
        },
    )

    assert out["strategy"]["metrics"]["trade_count"] == 1
    trade = out["strategy"]["trades"][0]
    assert trade["exit_reason"] == "stop_loss"
    assert trade["entry_date"] == str(idx[2].date())
    assert trade["return_pct"] == pytest.approx(-4.0)
