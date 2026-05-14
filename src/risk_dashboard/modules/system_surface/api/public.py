from __future__ import annotations

import json
import logging
import time
import urllib.request

import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from risk_dashboard.app.config.settings import get_settings
from risk_dashboard.data import cross_asset_prices as cross_asset_prices_mod
from risk_dashboard.platform.model_runtime.registry import model_runtime_health
from risk_dashboard.platform.runtime.panel_store import PanelUnavailableError, get_panel, panel_status
from risk_dashboard.quant.advanced_engine import (
    compute_garch_volatility,
    compute_market_regime,
    optimize_portfolio_allocation,
)
from risk_dashboard.quant.eod_pipeline import _get_cached_trained_model
from risk_dashboard.quant.xgb_engine import predict_horizons, prepare_features

logger = logging.getLogger(__name__)
router = APIRouter(tags=["System"])


def _dashboard_html() -> str:
    settings = get_settings()
    index_path = settings.frontend_dist / "index.html"
    html_path = index_path if index_path.exists() else settings.legacy_dashboard_html
    return html_path.read_text(encoding="utf-8")


def _get_live_vnindex_dnse(default_val: float) -> tuple[float, int]:
    start = int(time.time()) - 86400 * 2
    url = (
        f"https://services.entrade.com.vn/chart-api/v2/ohlcs/index"
        f"?resolution=1&symbol=VNINDEX&from={start}&to={int(time.time())}"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode())
            if "c" in data and len(data["c"]) > 0:
                return float(data["c"][-1]), int(data["t"][-1])
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError) as exc:
        logger.debug("Live VNINDEX fetch failed: %s", exc)
    return default_val, int(time.time())


@router.get("/health", tags=["System"])
def health() -> dict:
    status = panel_status()
    model = model_runtime_health()
    return {
        "status": "ok" if status["loaded"] else "degraded",
        "checks": {
            "panel_loaded": status["loaded"],
            "model_available": model["available"],
        },
    }


@router.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
def dashboard() -> str:
    return _dashboard_html()


@router.get("/", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/home", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/global-terminal", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/markets", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/news", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/news/economic-calendar", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/news-desk", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/learn", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/learning", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/simulation-lab", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/simulations", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/financial-statement-simulator", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/assignments", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/financial-health", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/goals", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/guided-investing", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/insights", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/community", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/pro-lab", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/backtest-studio", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/admin", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/admin/content-ops", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/admin/community", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/admin/pro-lab", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/admin/trust-safety", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/admin/analytics", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/login", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/register", response_class=HTMLResponse, tags=["Frontend"])
@router.get("/auth", response_class=HTMLResponse, tags=["Frontend"])
def frontend_app() -> str:
    return _dashboard_html()


@router.get("/dashboard/state", tags=["Dashboard"])
def dashboard_state() -> dict[str, object]:
    return panel_status()


@router.get("/dashboard/history", tags=["Dashboard"])
def dashboard_history(limit: int = 150):
    try:
        panel = get_panel()
    except PanelUnavailableError as exc:
        raise HTTPException(status_code=503, detail=exc.detail) from exc

    if panel.empty:
        return {"data": []}

    df = panel.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    trained_model, _ = _get_cached_trained_model(df, df["date"].max(), "skhgb-v4-hybrid", None, None, None)
    feat_df = prepare_features(df, vn30_panel=None).tail(limit)

    results = []
    for _, row in feat_df.iterrows():
        try:
            _, _, _, _, score = predict_horizons(trained_model, row)
            results.append(
                {
                    "time": row["date"].strftime("%Y-%m-%d"),
                    "value": float(row["vn_index"]),
                    "risk_score": float(score),
                }
            )
        except Exception:
            continue
    return {"data": results}


@router.get("/dashboard/cross-asset", tags=["Dashboard"])
def dashboard_cross_asset(limit: int = 180):
    if limit < 30 or limit > 365:
        raise HTTPException(status_code=400, detail="limit phải nằm trong khoảng 30..365")
    return cross_asset_prices_mod.build_cross_asset_dashboard(limit=limit)


@router.get("/dashboard/live", tags=["Dashboard"])
def dashboard_live():
    try:
        panel = get_panel()
    except PanelUnavailableError as exc:
        raise HTTPException(status_code=503, detail=exc.detail) from exc

    if panel.empty:
        return {}

    df = panel.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    last_row = df.iloc[-1].copy()
    base_price = float(last_row["vn_index"])
    current_vn_index, market_time = _get_live_vnindex_dnse(base_price)
    last_row["vn_index"] = current_vn_index
    last_row["date"] = pd.to_datetime(market_time, unit="s")
    df = pd.concat([df, pd.DataFrame([last_row])], ignore_index=True)

    trained_model, _ = _get_cached_trained_model(df, df["date"].max(), "skhgb-v4-hybrid", None, None, None)
    feat_df = prepare_features(df, vn30_panel=None)
    pred_row = feat_df.iloc[-1]
    _, _, _, _, score = predict_horizons(trained_model, pred_row)

    regime = compute_market_regime(df)
    vol_dict = compute_garch_volatility(df)
    alloc = optimize_portfolio_allocation(float(score), vol_dict["expected_volatility"])
    return {
        "time": market_time,
        "value": current_vn_index,
        "risk_score": float(score),
        "regime": regime,
        "lower_bound": vol_dict["lower_bound"],
        "upper_bound": vol_dict["upper_bound"],
        "stock_pct": alloc["stock_pct"],
        "cash_pct": alloc["cash_pct"],
    }


@router.get("/dashboard/money-flow", tags=["Dashboard"])
def dashboard_money_flow():
    return {
        "foreign_net_val": -450.5,
        "sectors": [
            {"name": "Ngân hàng", "flow": 520.4, "weight": 0.35},
            {"name": "Bất động sản", "flow": -310.2, "weight": 0.20},
            {"name": "Chứng khoán", "flow": 150.8, "weight": 0.15},
            {"name": "Thép", "flow": -85.5, "weight": 0.10},
            {"name": "Bán lẻ", "flow": 45.2, "weight": 0.08},
            {"name": "Dầu khí", "flow": -12.4, "weight": 0.07},
            {"name": "Công nghệ", "flow": 210.6, "weight": 0.05},
        ],
    }
