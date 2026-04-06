"""
Quant Risk Tool — Kết nối analytics.py + advanced_engine.py
Tất cả tính toán đều THẬT: VaR, CVaR, Monte Carlo, GARCH, Adaptive Conformal.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from langchain_core.tools import tool

# Singleton Adaptive Conformal tracker (sống xuyên suốt phiên server)
_conformal_tracker = None


def _get_conformal():
    global _conformal_tracker
    if _conformal_tracker is None:
        from risk_dashboard.quant.analytics import AdaptiveConformalVaR
        _conformal_tracker = AdaptiveConformalVaR(target_miscoverage=0.05)
    return _conformal_tracker


def _load_panel() -> pd.DataFrame | None:
    try:
        from risk_dashboard.api.main import get_panel
        return get_panel()
    except Exception:
        pass
    cache_dir = Path("data/cache")
    candidates = sorted(cache_dir.glob("panel_*.parquet"), key=lambda p: p.stat().st_mtime, reverse=True)
    return pd.read_parquet(candidates[0]) if candidates else None


@tool
def get_quant_risk_score() -> dict:
    """Tính toán Risk Score TOÀN DIỆN: HMM Regime, GARCH Volatility, VaR/CVaR (Historical + Monte Carlo),
    Sharpe/Sortino Ratio, XGBoost Risk Score, và trạng thái Adaptive Conformal.
    Trả về dict chứa tất cả chỉ số rủi ro hệ thống."""

    panel = _load_panel()
    results = {}

    if panel is None or panel.empty:
        return {"error": "Không có panel data. Hãy chạy EOD trước."}

    returns = panel["vn_index"].pct_change().dropna()

    # ── Analytics Engine (VaR, CVaR, Monte Carlo, Sharpe, Sortino, GARCH) ──
    try:
        from risk_dashboard.quant.analytics import full_risk_report
        results["analytics"] = full_risk_report(returns, confidence=0.95)
    except Exception as e:
        results["analytics_error"] = str(e)

    # ── HMM Market Regime ──
    try:
        from risk_dashboard.quant.advanced_engine import compute_market_regime
        results["market_regime"] = compute_market_regime(panel)
    except Exception as e:
        results["market_regime"] = f"Error: {e}"

    # ── XGBoost Risk Score ──
    try:
        from risk_dashboard.quant.eod_pipeline import _get_cached_trained_model
        from risk_dashboard.quant.xgb_engine import prepare_features, predict_horizons
        model_info = _get_cached_trained_model()
        if model_info and panel is not None:
            model_obj = model_info.get("model")
            feat_df = prepare_features(panel)
            if model_obj is not None and not feat_df.empty:
                h = predict_horizons(model_obj, feat_df)
                results["xgb_risk"] = {
                    "p_decline_1w": round(float(h.p_decline_1w), 4),
                    "p_decline_2w": round(float(h.p_decline_2w), 4),
                    "expected_drawdown_pct": round(float(h.expected_drawdown_pct), 4),
                }
    except Exception as e:
        results["xgb_risk_error"] = str(e)

    # ── Adaptive Conformal Status ──
    try:
        tracker = _get_conformal()
        results["adaptive_conformal"] = tracker.get_summary()
    except Exception as e:
        results["adaptive_conformal_error"] = str(e)

    results["source"] = "analytics.py + advanced_engine.py + XGBoost"
    return results


@tool
def run_what_if_simulation(usd_vnd_rate: float) -> dict:
    """Chạy mô phỏng kịch bản What-if THẬT bằng Scenario Engine.
    Input: usd_vnd_rate (ví dụ 26000.0).
    Trả về Risk Score trước/sau khi thay đổi tỷ giá."""
    try:
        from risk_dashboard.quant.scenario import rerun_with_macro_override
        result = rerun_with_macro_override(usd_vnd_rate=usd_vnd_rate)
        return {"scenario": f"USD/VND = {usd_vnd_rate:,.0f}", "result": result, "source": "Scenario Engine"}
    except Exception as e:
        return {"error": f"Mô phỏng thất bại: {e}"}


@tool
def compute_stock_risk_metrics(ticker: str) -> dict:
    """Tính VaR, CVaR, Beta, Sharpe, Sortino cho MỘT mã cổ phiếu cụ thể.
    Input: ticker (ví dụ 'FPT'). Kéo dữ liệu thật từ yfinance rồi chạy analytics."""
    try:
        import yfinance as yf
        from risk_dashboard.quant.analytics import (
            historical_var, historical_cvar, monte_carlo_var,
            sharpe_ratio, sortino_ratio, compute_beta, garch_forecast,
            amihud_illiquidity,
        )

        # Lấy giá cổ phiếu
        stock = yf.Ticker(f"{ticker.upper()}.VN")
        hist = stock.history(period="1y", auto_adjust=True)
        if hist is None or hist.empty:
            return {"error": f"Không có dữ liệu giá cho {ticker}.VN"}
        stock_ret = hist["Close"].pct_change().dropna()

        # Lấy VN-Index làm benchmark
        bench = yf.Ticker("^VNINDEX")
        bench_hist = bench.history(period="1y", auto_adjust=True)
        bench_ret = bench_hist["Close"].pct_change().dropna() if bench_hist is not None else pd.Series()

        beta_val = compute_beta(stock_ret, bench_ret) if not bench_ret.empty else None

        return {
            "ticker": ticker.upper(),
            "n_days": len(stock_ret),
            "var_95": round(historical_var(stock_ret, 0.95), 6),
            "cvar_95": round(historical_cvar(stock_ret, 0.95), 6),
            "monte_carlo_var": monte_carlo_var(stock_ret, confidence=0.95, horizon_days=5),
            "beta_vs_vnindex": beta_val,
            "sharpe_ratio": sharpe_ratio(stock_ret),
            "sortino_ratio": sortino_ratio(stock_ret),
            "garch_forecast": garch_forecast(stock_ret),
            "amihud_illiquidity": amihud_illiquidity(stock_ret, hist["Volume"]) if "Volume" in hist.columns else None,
            "source": f"yfinance ({ticker}.VN) + analytics.py",
        }
    except Exception as e:
        return {"error": f"Không thể tính risk metrics cho {ticker}: {e}"}


@tool
def run_stress_test() -> dict:
    """Chạy Stress Testing trên toàn bộ thị trường (VN-Index).
    Mô phỏng các kịch bản Thiên nga đen: COVID, Lehman, ASEAN Crisis 1997, Black Monday.
    Trả về mức lỗ ước tính và số ngày phục hồi cho mỗi kịch bản."""
    panel = _load_panel()
    if panel is None or panel.empty:
        return {"error": "Không có panel data."}

    returns = panel["vn_index"].pct_change().dropna()
    try:
        from risk_dashboard.quant.analytics import stress_test_portfolio
        return stress_test_portfolio(returns)
    except Exception as e:
        return {"error": f"Stress test thất bại: {e}"}


@tool
def run_var_backtest() -> dict:
    """Kiểm định chất lượng mô hình VaR bằng Kupiec POF Test và Christoffersen Independence Test.
    Đây là bài kiểm tra theo chuẩn Basel III để xác minh mô hình VaR có đạt chuẩn không.
    Trả về kết quả kiểm định, Basel Traffic Light (Green/Yellow/Red), và tính cụm vi phạm."""
    panel = _load_panel()
    if panel is None or panel.empty:
        return {"error": "Không có panel data."}

    returns = panel["vn_index"].pct_change().dropna()
    try:
        from risk_dashboard.quant.analytics import (
            historical_var, kupiec_pof_test, christoffersen_interval_test,
        )

        # Backtest VaR 95% trên toàn bộ dữ liệu (walk-forward)
        window = 250  # 1 năm lịch sử
        violations = []
        for i in range(window, len(returns)):
            hist_window = returns.iloc[i - window:i]
            var_pred = historical_var(hist_window, 0.95)
            actual_loss = -float(returns.iloc[i])  # Dương = lỗ
            violations.append(1 if actual_loss > var_pred else 0)

        n_violations = sum(violations)
        n_obs = len(violations)

        kupiec = kupiec_pof_test(n_violations, n_obs, confidence=0.95)
        christoffersen = christoffersen_interval_test(violations)

        return {
            "backtest_window": window,
            "total_observations": n_obs,
            "total_violations": n_violations,
            "kupiec_test": kupiec,
            "christoffersen_test": christoffersen,
            "source": "analytics.py (walk-forward backtest)",
        }
    except Exception as e:
        return {"error": f"Backtest thất bại: {e}"}

