"""
Backtest buy-and-hold danh mục cổ phiếu VN (giá điều chỉnh qua yfinance).

Không mô phỏng phí giao dịch, trượt giá hay tái cân bằng — chỉ để người dùng
ước lượng đường cong vốn lịch sử trên dữ liệu công khai.
"""
from __future__ import annotations

import logging
import re
from datetime import date, timedelta
from typing import Any

import numpy as np
import pandas as pd

from risk_dashboard.quant.analytics import (
    compute_beta,
    historical_cvar,
    historical_var,
    information_ratio,
    sharpe_ratio,
    sortino_ratio,
)

logger = logging.getLogger(__name__)

_MAX_TICKERS = 30
_MAX_RANGE_DAYS = 365 * 10
# Lãi phi rủi năm (dùng cho Sharpe/Sortino/Jensen alpha) — đồng bộ với analytics mặc định
RISK_FREE_ANNUAL = 0.045
_MIN_DAYS_VAR = 30
_MIN_DAYS_BENCHMARK_RELATIVE = 30
_ROLLING_VOL_WINDOW = 21
_DEFAULT_BTC_SYMBOL = "BTC-USD"


def _clean_ticker(raw: str) -> str:
    t = re.sub(r"[^A-Za-z0-9]", "", raw.strip()).upper()
    return t


def parse_ticker_list(tickers: list[str]) -> list[str]:
    out: list[str] = []
    for x in tickers:
        t = _clean_ticker(x)
        if t and t not in out:
            out.append(t)
    if not out:
        raise ValueError("Cần ít nhất một mã hợp lệ.")
    if len(out) > _MAX_TICKERS:
        raise ValueError(f"Tối đa {_MAX_TICKERS} mã.")
    return out


def normalize_weights(
    tickers: list[str],
    *,
    equal_weight: bool,
    weights: dict[str, float] | None,
) -> dict[str, float]:
    if equal_weight or not weights:
        w = 1.0 / len(tickers)
        return {t: w for t in tickers}

    cleaned: dict[str, float] = {}
    for k, v in weights.items():
        tk = _clean_ticker(k)
        if tk in tickers:
            cleaned[tk] = float(v)

    if set(cleaned.keys()) != set(tickers):
        missing = set(tickers) - set(cleaned.keys())
        raise ValueError(f"Thiếu trọng số cho các mã: {', '.join(sorted(missing))}")

    s = sum(cleaned.values())
    if s <= 0:
        raise ValueError("Tổng trọng số phải > 0.")
    return {k: cleaned[k] / s for k in tickers}


def _yf_symbol(ticker: str) -> str:
    return f"{ticker.upper()}.VN"


def _normalize_ohlcv_frame(raw: pd.DataFrame) -> pd.DataFrame:
    if raw is None or raw.empty:
        return pd.DataFrame()

    df = raw.rename(columns=lambda c: str(c).lower())
    needed = ("open", "high", "low", "close", "volume")
    if any(col not in df.columns for col in needed):
        return pd.DataFrame()

    out = df[list(needed)].copy()
    idx = pd.to_datetime(out.index)
    if hasattr(idx, "tz") and idx.tz is not None:
        idx = idx.tz_localize(None)
    out.index = idx.normalize()
    out = out[~out.index.duplicated(keep="last")]
    out = out.sort_index()
    for col in needed:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out.dropna(how="any")


def _ohlcv_frames_from_download(raw: pd.DataFrame, symbols_plain: list[str]) -> dict[str, pd.DataFrame]:
    if raw is None or raw.empty:
        raise ValueError("Không có dữ liệu OHLCV.")

    if isinstance(raw.columns, pd.MultiIndex):
        out: dict[str, pd.DataFrame] = {}
        for ticker in symbols_plain:
            symbol = _yf_symbol(ticker)
            cols: dict[str, pd.Series] = {}
            for field in ("Open", "High", "Low", "Close", "Volume"):
                key = (field, symbol)
                if key not in raw.columns:
                    raise ValueError(f"Thiếu dữ liệu {field} cho {ticker} ({symbol}).")
                cols[field.lower()] = raw[key]
            frame = _normalize_ohlcv_frame(pd.DataFrame(cols))
            if frame.empty:
                raise ValueError(f"Không chuẩn hóa được OHLCV cho {ticker}.")
            out[ticker] = frame
        return out

    ticker = symbols_plain[0]
    frame = _normalize_ohlcv_frame(raw)
    if frame.empty:
        raise ValueError(f"Không chuẩn hóa được OHLCV cho {ticker}.")
    return {ticker: frame}


def _close_to_df(raw: pd.DataFrame, symbols_plain: list[str]) -> pd.DataFrame:
    """Chuẩn hóa output yfinance thành DataFrame cột = mã (không .VN)."""
    if raw is None or raw.empty:
        raise ValueError("Không có dữ liệu giá.")

    if "Close" not in raw.columns:
        raise ValueError("Thiếu cột Close trong dữ liệu giá.")

    close = raw["Close"]
    if isinstance(close, pd.Series):
        return close.to_frame(name=symbols_plain[0])

    # DataFrame: cột là mã yfinance (FPT.VN, ...)
    out = pd.DataFrame()
    for t in symbols_plain:
        col = _yf_symbol(t)
        if col not in close.columns:
            raise ValueError(f"Không tìm thấy cột giá cho {t} ({col}).")
        out[t] = close[col]
    return out


def fetch_vn_close_separate_benchmark(
    tickers: list[str],
    start: date,
    end: date,
) -> tuple[pd.DataFrame, pd.Series | None]:
    """Tải giá cổ phiếu VN và chuỗi VN-Index riêng (symbol khác định dạng)."""
    import yfinance as yf

    stock_syms = [_yf_symbol(t) for t in tickers]
    end_adj = end + timedelta(days=1)

    raw_stocks = yf.download(
        stock_syms,
        start=start,
        end=end_adj,
        auto_adjust=True,
        progress=False,
        threads=True,
    )
    stocks = _close_to_df(raw_stocks, tickers)
    bench_close: pd.Series | None = None
    try:
        raw_b = yf.download(
            "^VNINDEX",
            start=start,
            end=end_adj,
            auto_adjust=True,
            progress=False,
        )
        if raw_b is not None and not raw_b.empty and "Close" in raw_b.columns:
            bench_close = raw_b["Close"].squeeze()
            if isinstance(bench_close, pd.DataFrame):
                bench_close = bench_close.iloc[:, 0]
    except Exception as exc:
        logger.info("Benchmark ^VNINDEX không tải được: %s", exc)

    return stocks, bench_close


def fetch_vn_stocks_only(tickers: list[str], start: date, end: date) -> pd.DataFrame:
    """Chỉ tải cổ phiếu VN (không gọi benchmark)."""
    import yfinance as yf

    stock_syms = [_yf_symbol(t) for t in tickers]
    end_adj = end + timedelta(days=1)
    raw_stocks = yf.download(
        stock_syms,
        start=start,
        end=end_adj,
        auto_adjust=True,
        progress=False,
        threads=True,
    )
    return _close_to_df(raw_stocks, tickers)


def fetch_vn_ohlcv_with_regime_inputs(
    tickers: list[str],
    start: date,
    end: date,
    *,
    include_benchmark: bool,
) -> tuple[dict[str, pd.DataFrame], pd.Series | None, pd.Series]:
    """Tải OHLCV cho cổ phiếu VN + benchmark tùy chọn + chuỗi BTC xác nhận risk-on."""
    import yfinance as yf

    stock_syms = [_yf_symbol(t) for t in tickers]
    end_adj = end + timedelta(days=1)

    raw_stocks = yf.download(
        stock_syms,
        start=start,
        end=end_adj,
        auto_adjust=True,
        progress=False,
        threads=True,
    )
    stock_frames = _ohlcv_frames_from_download(raw_stocks, tickers)

    bench_close: pd.Series | None = None
    if include_benchmark:
        try:
            raw_b = yf.download(
                "^VNINDEX",
                start=start,
                end=end_adj,
                auto_adjust=True,
                progress=False,
            )
            if raw_b is not None and not raw_b.empty and "Close" in raw_b.columns:
                bench_close = raw_b["Close"].squeeze()
                if isinstance(bench_close, pd.DataFrame):
                    bench_close = bench_close.iloc[:, 0]
        except Exception as exc:
            logger.info("Benchmark ^VNINDEX không tải được: %s", exc)

    raw_btc = yf.download(
        _DEFAULT_BTC_SYMBOL,
        start=start - timedelta(days=7),
        end=end_adj,
        auto_adjust=True,
        progress=False,
    )
    if raw_btc is None or raw_btc.empty or "Close" not in raw_btc.columns:
        raise ValueError("Không tải được dữ liệu BTC-USD để xác nhận tín hiệu chiến lược.")
    btc_close = raw_btc["Close"].squeeze()
    if isinstance(btc_close, pd.DataFrame):
        btc_close = btc_close.iloc[:, 0]
    btc_close.index = pd.to_datetime(btc_close.index).tz_localize(None)
    btc_close = btc_close.sort_index()

    return stock_frames, bench_close, btc_close


def compute_buy_and_hold(
    close: pd.DataFrame,
    weights: dict[str, float],
    initial_capital: float,
    *,
    benchmark_close: pd.Series | None = None,
) -> dict[str, Any]:
    """
    close: hàng = ngày, cột = mã (đã align).
    Trả về metrics + chuỗi equity (VNĐ) và benchmark cùng vốn ban đầu (nếu có).
    """
    if close.shape[1] < 1:
        raise ValueError("Bảng giá rỗng.")

    ordered = [c for c in close.columns if c in weights]
    if len(ordered) != len(weights):
        raise ValueError("Cột giá và trọng số không khớp.")

    sub = close[ordered].copy()
    sub = sub.sort_index()
    sub = sub.dropna(how="any")
    if len(sub) < 20:
        raise ValueError("Không đủ ngày giao dịch sau khi căn chỉnh (cần >= 20).")

    daily_ret = sub.pct_change().dropna()
    if daily_ret.empty:
        raise ValueError("Không tính được lợi suất ngày.")

    w = np.array([weights[c] for c in ordered])
    port_ret = (daily_ret.values * w).sum(axis=1)
    port_ret = pd.Series(port_ret, index=daily_ret.index)

    equity_curve = float(initial_capital) * (1.0 + port_ret).cumprod()

    summary = _summarize_equity_curve(
        equity_curve,
        initial_capital=float(initial_capital),
        benchmark_close=benchmark_close,
        warnings=[],
    )
    hhi = float(sum(float(weights[k]) ** 2 for k in weights))
    summary["metrics"]["concentration_herfindahl"] = round(hhi, 4)
    return summary


def _summarize_equity_curve(
    equity_curve: pd.Series,
    *,
    initial_capital: float,
    benchmark_close: pd.Series | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    warnings = list(warnings or [])
    equity_curve = equity_curve.sort_index().dropna()
    if len(equity_curve) < 2:
        raise ValueError("Không đủ dữ liệu đường vốn để tính metrics.")

    port_ret = equity_curve.pct_change().dropna()
    if port_ret.empty:
        raise ValueError("Không tính được lợi suất ngày từ đường vốn.")

    peak = equity_curve.cummax()
    dd = (equity_curve / peak - 1.0) * 100.0
    max_dd_pct = float(dd.min()) if len(dd) else 0.0

    total_return_pct = float((equity_curve.iloc[-1] / float(initial_capital) - 1.0) * 100.0)
    n_days = int(len(equity_curve))
    years = n_days / 252.0
    if years > 0 and float(initial_capital) > 0:
        cagr_pct = float((equity_curve.iloc[-1] / float(initial_capital)) ** (1.0 / years) - 1.0) * 100.0
    else:
        cagr_pct = float("nan")

    vol_pct = float(port_ret.std() * np.sqrt(252) * 100.0) if port_ret.std() > 0 else float("nan")

    sharpe = sharpe_ratio(port_ret, RISK_FREE_ANNUAL)
    sortino = sortino_ratio(port_ret, RISK_FREE_ANNUAL)

    var_95_pct: float | None = None
    cvar_95_pct: float | None = None
    if len(port_ret) >= _MIN_DAYS_VAR:
        v = historical_var(port_ret, 0.95)
        cv = historical_cvar(port_ret, 0.95)
        if np.isfinite(v):
            var_95_pct = round(float(v) * 100.0, 4)
        if np.isfinite(cv):
            cvar_95_pct = round(float(cv) * 100.0, 4)

    roll = port_ret.rolling(_ROLLING_VOL_WINDOW).std() * np.sqrt(252) * 100.0
    rolling_vol_annual_pct = [
        {"time": _to_ts(idx), "value": round(float(v), 2)}
        for idx, v in roll.items()
        if np.isfinite(v)
    ]

    series_port = [{"time": _to_ts(idx), "value": round(float(v), 2)} for idx, v in equity_curve.items()]

    bench_series: list[dict[str, float]] | None = None

    if benchmark_close is not None and not benchmark_close.empty:
        bench = benchmark_close.reindex(equity_curve.index).ffill().dropna()
        common = bench.index.intersection(equity_curve.index)
        if len(common) >= 20:
            bench = bench.loc[common]
            ec = equity_curve.loc[common]
            first_b = float(bench.iloc[0])
            if first_b > 0:
                shares = float(initial_capital) / first_b
                bench_equity = shares * bench
                bench_series = [
                    {"time": _to_ts(idx), "value": round(float(v), 2)}
                    for idx, v in bench_equity.items()
                ]
            else:
                warnings.append("VN-Index có giá không hợp lệ tại ngày đầu, bỏ benchmark.")
        else:
            warnings.append("Không đủ ngày chung với VN-Index để vẽ benchmark.")

    alpha_annual_pct: float | None = None
    beta_vs_benchmark: float | None = None
    tracking_error_annual_pct: float | None = None
    information_ratio_vs_bench: float | None = None
    if benchmark_close is not None and not benchmark_close.empty:
        bench_aligned = benchmark_close.reindex(port_ret.index).ffill()
        bench_ret = bench_aligned.pct_change()
        aligned = pd.DataFrame({"p": port_ret, "b": bench_ret}).dropna()
        if len(aligned) >= _MIN_DAYS_BENCHMARK_RELATIVE:
            b = compute_beta(aligned["p"], aligned["b"])
            if np.isfinite(b):
                beta_vs_benchmark = round(float(b), 4)
                rf_d = RISK_FREE_ANNUAL / 252.0
                alpha_d = aligned["p"].mean() - rf_d - float(b) * (aligned["b"].mean() - rf_d)
                alpha_annual_pct = round(float(alpha_d * 252 * 100.0), 4)
            active = aligned["p"] - aligned["b"]
            if len(active) > 1 and active.std() and active.std() > 0:
                tracking_error_annual_pct = round(float(active.std() * np.sqrt(252) * 100.0), 4)
            ir = information_ratio(aligned["p"], aligned["b"])
            if np.isfinite(ir):
                information_ratio_vs_bench = float(ir)

    return {
        "metrics": {
            "total_return_pct": round(total_return_pct, 2),
            "cagr_pct": round(cagr_pct, 2) if np.isfinite(cagr_pct) else None,
            "volatility_annual_pct": round(vol_pct, 2) if np.isfinite(vol_pct) else None,
            "max_drawdown_pct": round(max_dd_pct, 2),
            "sharpe": sharpe if np.isfinite(sharpe) else None,
            "sortino": sortino if np.isfinite(sortino) else None,
            "risk_free_annual_pct": round(RISK_FREE_ANNUAL * 100.0, 2),
            "var_95_daily_pct": var_95_pct,
            "cvar_95_daily_pct": cvar_95_pct,
            "alpha_annual_pct_jensen": alpha_annual_pct,
            "beta_vs_benchmark": beta_vs_benchmark,
            "tracking_error_annual_pct": tracking_error_annual_pct,
            "information_ratio_vs_benchmark": information_ratio_vs_bench,
            "trading_days": n_days,
            "first_date": str(equity_curve.index[0].date()),
            "last_date": str(equity_curve.index[-1].date()),
        },
        "series": {
            "portfolio": series_port,
            "benchmark": bench_series,
            "drawdown_pct": equity_drawdown_series(equity_curve),
            "rolling_vol_annual_pct": rolling_vol_annual_pct,
        },
        "monthly_returns": monthly_equity_returns(equity_curve),
        "ath_segments": ath_interval_segments(equity_curve),
        "warnings": warnings,
    }


def _to_ts(idx: pd.Timestamp) -> int:
    ts = pd.Timestamp(idx)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return int(ts.timestamp())


def equity_drawdown_series(equity: pd.Series) -> list[dict[str, Any]]:
    """Đường drawdown % so với đỉnh chạy (≤ 0)."""
    peak = equity.cummax()
    dd = (equity / peak - 1.0) * 100.0
    return [{"time": _to_ts(idx), "value": round(float(v), 2)} for idx, v in dd.items()]


def monthly_equity_returns(equity: pd.Series) -> list[dict[str, Any]]:
    """Lợi suất theo tháng (cuối tháng so với cuối tháng trước; tháng đầu so với ngày đầu chuỗi)."""
    if equity.empty:
        return []
    me = equity.resample("ME").last().dropna()
    if me.empty:
        return []
    out: list[dict[str, Any]] = []
    for i, (dt, val) in enumerate(me.items()):
        if i == 0:
            rp = (float(val) / float(equity.iloc[0]) - 1.0) * 100.0
        else:
            rp = (float(val) / float(me.iloc[i - 1]) - 1.0) * 100.0
        out.append(
            {
                "time": _to_ts(pd.Timestamp(dt)),
                "period": pd.Timestamp(dt).strftime("%Y-%m"),
                "return_pct": round(rp, 3),
            }
        )
    return out


def ath_interval_segments(equity: pd.Series) -> list[dict[str, Any]]:
    """
    Giữa hai lần vốn chạm đỉnh lịch sử (ATH) liên tiếp trên chuỗi **cuối tháng**:
    trong khoảng đó tìm đáy (ngày) trên chuỗi ngày gốc — tránh mỗi phiên đều là "ATH" khi giá tăng đều.
    """
    if len(equity) < 20:
        return []

    me = equity.resample("ME").last().dropna()
    if len(me) < 3:
        return []

    cm = me.cummax()
    new_high = (cm.diff() > 0).fillna(False)
    new_high.iloc[0] = True
    ath_idx = list(me.index[new_high.to_numpy()])
    if len(ath_idx) < 2:
        return []

    segments: list[dict[str, Any]] = []
    for i in range(len(ath_idx) - 1):
        d0, d1 = ath_idx[i], ath_idx[i + 1]
        v_peak = float(me.loc[d0])
        v_next = float(me.loc[d1])
        window = equity.loc[d0:d1]
        if window.empty:
            continue
        trough_val = float(window.min())
        trough_dt = window.idxmin()
        dd_pct = (trough_val / v_peak - 1.0) * 100.0 if v_peak > 0 else 0.0
        rec_pct = (v_next / trough_val - 1.0) * 100.0 if trough_val > 0 else 0.0
        days = int((pd.Timestamp(d1) - pd.Timestamp(d0)).days)
        segments.append(
            {
                "segment_index": i + 1,
                "from_ath_date": str(pd.Timestamp(d0).date()),
                "to_next_ath_date": str(pd.Timestamp(d1).date()),
                "peak_value": round(v_peak, 2),
                "trough_date": str(pd.Timestamp(trough_dt).date()),
                "trough_value": round(trough_val, 2),
                "drawdown_pct": round(dd_pct, 2),
                "recovery_to_next_ath_pct": round(rec_pct, 2),
                "calendar_days": days,
            }
        )
    return segments


def validate_date_range(start: date, end: date) -> None:
    if end <= start:
        raise ValueError("end_date phải sau start_date.")
    if (end - start).days > _MAX_RANGE_DAYS:
        raise ValueError(f"Khoảng thời gian tối đa {_MAX_RANGE_DAYS // 365} năm.")


def _clean_strategy_config(strategy: dict[str, Any] | None) -> dict[str, float]:
    raw = dict(strategy or {})
    return {
        "volume_spike_multiplier": float(raw.get("volume_spike_multiplier", 2.0)),
        "btc_daily_change_min_pct": float(raw.get("btc_daily_change_min_pct", 3.0)),
        "stop_loss_pct": float(raw.get("stop_loss_pct", 4.0)),
    }


def _validate_strategy_config(config: dict[str, float]) -> None:
    if config["volume_spike_multiplier"] < 1.0:
        raise ValueError("volume_spike_multiplier phải >= 1.0.")
    if not (-50.0 <= config["btc_daily_change_min_pct"] <= 50.0):
        raise ValueError("btc_daily_change_min_pct phải nằm trong [-50, 50].")
    if not (0.1 <= config["stop_loss_pct"] <= 50.0):
        raise ValueError("stop_loss_pct phải nằm trong [0.1, 50].")


def backtest_volume_btc_stoploss_strategy(
    stock_frames: dict[str, pd.DataFrame],
    weights: dict[str, float],
    initial_capital: float,
    *,
    btc_close: pd.Series,
    benchmark_close: pd.Series | None,
    config: dict[str, float],
) -> dict[str, Any]:
    _validate_strategy_config(config)

    per_ticker_equity: dict[str, pd.Series] = {}
    trades: list[dict[str, Any]] = []

    for ticker, frame in stock_frames.items():
        df = frame.copy().sort_index()
        if len(df) < 5:
            raise ValueError(f"Không đủ OHLCV cho {ticker} để chạy chiến lược.")

        btc_aligned = btc_close.reindex(df.index).ffill()
        btc_ret_pct = btc_aligned.pct_change() * 100.0
        vol_multiple = df["volume"] / df["volume"].shift(1)

        sleeve_capital = float(initial_capital) * float(weights[ticker])
        cash = sleeve_capital
        shares = 0.0
        in_position = False
        entry_price = 0.0
        entry_date: pd.Timestamp | None = None
        stop_price = 0.0
        pending_signal: dict[str, float] | None = None
        active_signal_meta: dict[str, float] | None = None
        equity_points: list[tuple[pd.Timestamp, float]] = []

        for i, (dt, row) in enumerate(df.iterrows()):
            if pending_signal and not in_position:
                buy_price = float(row["open"])
                if buy_price > 0:
                    active_signal_meta = pending_signal
                    shares = cash / buy_price
                    cash = 0.0
                    in_position = True
                    entry_price = buy_price
                    entry_date = pd.Timestamp(dt)
                    stop_price = entry_price * (1.0 - config["stop_loss_pct"] / 100.0)
                    pending_signal = None

            exit_reason: str | None = None
            exit_price: float | None = None
            if in_position:
                low = float(row["low"])
                close_price = float(row["close"])
                if low <= stop_price:
                    exit_reason = "stop_loss"
                    exit_price = stop_price
                elif i == len(df) - 1:
                    exit_reason = "end_of_test"
                    exit_price = close_price

                if exit_reason and exit_price is not None and entry_date is not None:
                    cash = shares * exit_price
                    trades.append(
                        {
                            "ticker": ticker,
                            "entry_date": str(entry_date.date()),
                            "entry_price": round(float(entry_price), 4),
                            "exit_date": str(pd.Timestamp(dt).date()),
                            "exit_price": round(float(exit_price), 4),
                            "return_pct": round((float(exit_price) / float(entry_price) - 1.0) * 100.0, 3),
                            "exit_reason": exit_reason,
                            "holding_days": int((pd.Timestamp(dt) - entry_date).days),
                            "signal_volume_multiple": round(float(active_signal_meta["signal_volume_multiple"]), 3)
                            if active_signal_meta and "signal_volume_multiple" in active_signal_meta
                            else None,
                            "signal_btc_change_pct": round(float(active_signal_meta["signal_btc_change_pct"]), 3)
                            if active_signal_meta and "signal_btc_change_pct" in active_signal_meta
                            else None,
                        }
                    )
                    shares = 0.0
                    in_position = False
                    entry_price = 0.0
                    stop_price = 0.0
                    entry_date = None
                    active_signal_meta = None

            signal_today = (
                not in_position
                and pending_signal is None
                and i < len(df) - 1
                and pd.notna(vol_multiple.iloc[i])
                and pd.notna(btc_ret_pct.iloc[i])
                and float(vol_multiple.iloc[i]) >= config["volume_spike_multiplier"]
                and float(btc_ret_pct.iloc[i]) >= config["btc_daily_change_min_pct"]
            )
            if signal_today:
                pending_signal = {
                    "signal_volume_multiple": float(vol_multiple.iloc[i]),
                    "signal_btc_change_pct": float(btc_ret_pct.iloc[i]),
                }

            equity_value = cash if not in_position else shares * float(row["close"])
            equity_points.append((pd.Timestamp(dt), float(equity_value)))

        per_ticker_equity[ticker] = pd.Series(
            [value for _, value in equity_points],
            index=[idx for idx, _ in equity_points],
            name=ticker,
        )

    if not per_ticker_equity:
        raise ValueError("Không có chuỗi vốn nào được tạo từ chiến lược.")

    equity_df = pd.concat(per_ticker_equity.values(), axis=1).sort_index().ffill().fillna(0.0)
    total_equity = equity_df.sum(axis=1)
    summary = _summarize_equity_curve(
        total_equity,
        initial_capital=float(initial_capital),
        benchmark_close=benchmark_close,
        warnings=[],
    )

    hhi = float(sum(float(weights[k]) ** 2 for k in weights))
    total_trades = len(trades)
    win_rate = (
        sum(1 for trade in trades if float(trade["return_pct"]) > 0) / total_trades * 100.0
        if total_trades
        else None
    )
    avg_holding = (
        sum(int(trade["holding_days"]) for trade in trades) / total_trades if total_trades else None
    )
    exposure_days = sum(int(trade["holding_days"]) for trade in trades)

    summary["metrics"]["concentration_herfindahl"] = round(hhi, 4)
    summary["strategy"] = {
        "enabled": True,
        "name": "volume_spike_btc_confirm_stop_loss",
        "config": {
            "volume_spike_multiplier": round(config["volume_spike_multiplier"], 4),
            "btc_daily_change_min_pct": round(config["btc_daily_change_min_pct"], 4),
            "stop_loss_pct": round(config["stop_loss_pct"], 4),
        },
        "metrics": {
            "trade_count": total_trades,
            "win_rate_pct": round(win_rate, 2) if win_rate is not None else None,
            "avg_holding_days": round(avg_holding, 2) if avg_holding is not None else None,
            "exposure_days_sum": int(exposure_days),
        },
        "trades": trades,
    }
    return summary


def run_vn_portfolio_backtest(
    tickers: list[str],
    start: date,
    end: date,
    initial_capital: float,
    *,
    equal_weight: bool = True,
    weights: dict[str, float] | None = None,
    include_benchmark: bool = True,
    strategy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Tải giá yfinance + chạy buy-and-hold."""
    validate_date_range(start, end)
    tix = parse_ticker_list(tickers)
    w = normalize_weights(tix, equal_weight=equal_weight, weights=weights)
    strategy_cfg = dict(strategy or {})

    if strategy_cfg:
        stock_frames, bench_raw, btc_close = fetch_vn_ohlcv_with_regime_inputs(
            tix,
            start,
            end,
            include_benchmark=include_benchmark,
        )
        result = backtest_volume_btc_stoploss_strategy(
            stock_frames,
            w,
            initial_capital,
            btc_close=btc_close,
            benchmark_close=bench_raw if include_benchmark else None,
            config=_clean_strategy_config(strategy_cfg),
        )
    else:
        if include_benchmark:
            stocks, bench_raw = fetch_vn_close_separate_benchmark(tix, start, end)
        else:
            stocks = fetch_vn_stocks_only(tix, start, end)
            bench_raw = None

        result = compute_buy_and_hold(
            stocks,
            w,
            initial_capital,
            benchmark_close=bench_raw if include_benchmark else None,
        )

    payload = {
        "tickers": tix,
        "weights": {k: round(v, 6) for k, v in w.items()},
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "initial_capital": float(initial_capital),
        "metrics": result["metrics"],
        "series": result["series"],
        "monthly_returns": result.get("monthly_returns", []),
        "ath_segments": result.get("ath_segments", []),
        "benchmark_label": "VN-Index (^VNINDEX), cùng vốn ban đầu" if include_benchmark else None,
        "warnings": result["warnings"],
        "source": "yfinance (auto_adjust)",
    }
    if result.get("strategy"):
        payload["strategy"] = result["strategy"]
    return payload
