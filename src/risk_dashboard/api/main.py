from __future__ import annotations

import json
import logging
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from risk_dashboard.agents.graph import AgentState, run_eod_narrative
from risk_dashboard.agents.multi_agent import run_chat
from risk_dashboard.data.financials import (
    FinancialDataError,
    get_financial_dataset,
    import_financial_dataset,
)
from risk_dashboard.quant.advanced_engine import (
    compute_garch_volatility,
    compute_market_regime,
    optimize_portfolio_allocation,
)
from risk_dashboard.quant.eod_pipeline import _get_cached_trained_model
from risk_dashboard.quant.financial_analysis import analyze_financial_dataset
from risk_dashboard.quant.research_report import build_model_research_report
from risk_dashboard.quant.scenario import rerun_with_macro_override
from risk_dashboard.quant.xgb_engine import prepare_features, predict_horizons
from risk_dashboard.schemas.financials import FinancialImportRequest

from risk_dashboard.api.middleware import APIKeyMiddleware, RequestLoggingMiddleware

logger = logging.getLogger(__name__)

_TAGS_METADATA = [
    {"name": "System", "description": "Health checks and system state"},
    {"name": "Dashboard", "description": "Chart data, live feed, money flow"},
    {"name": "Quant", "description": "EOD pipeline and scenario simulation"},
    {"name": "Chat", "description": "Multi-agent LLM chat"},
    {"name": "Financials", "description": "Financial statement analysis"},
    {"name": "Admin", "description": "Panel management"},
]

app = FastAPI(
    title="Risk Dashboard API",
    version="0.1.0",
    description="Neural-symbolic risk pipeline for Vietnamese equity market",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=_TAGS_METADATA,
)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(APIKeyMiddleware)
_LEGACY_DASHBOARD_HTML = Path(__file__).with_name("dashboard.html")
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_FRONTEND_DIST = _PROJECT_ROOT / "frontend" / "dist"

if _FRONTEND_DIST.exists():
    app.mount("/dashboard-static", StaticFiles(directory=_FRONTEND_DIST), name="dashboard-static")


def _dashboard_html_path() -> Path:
    index_path = _FRONTEND_DIST / "index.html"
    if index_path.exists():
        return index_path
    return _LEGACY_DASHBOARD_HTML

# Demo in-memory panel — thay bằng DB trong production
_PANEL: pd.DataFrame | None = None
_PANEL_SOURCE: str | None = None
_PANEL_LOAD_ERROR: str | None = None
_PANEL_LOAD_HINT: str | None = None


def _set_panel_load_diagnostics(error: str | None, hint: str | None = None) -> None:
    global _PANEL_LOAD_ERROR, _PANEL_LOAD_HINT
    _PANEL_LOAD_ERROR = error
    _PANEL_LOAD_HINT = hint


def _panel_not_loaded_detail() -> dict[str, str]:
    detail = {
        "message": "Panel not loaded",
        "error": _PANEL_LOAD_ERROR or "Backend chưa nạp được training panel.",
        "hint": _PANEL_LOAD_HINT
        or "Tạo lại panel parquet trong `data/cache` rồi restart backend.",
    }
    return detail


def get_panel() -> pd.DataFrame:
    if _PANEL is None:
        raise HTTPException(status_code=503, detail=_panel_not_loaded_detail())
    return _PANEL


def set_panel_for_testing(df: pd.DataFrame) -> None:
    global _PANEL, _PANEL_SOURCE
    _PANEL = df
    _PANEL_SOURCE = "testing"
    _set_panel_load_diagnostics(None, None)


def set_panel_from_frame(df: pd.DataFrame, *, source: str) -> None:
    global _PANEL, _PANEL_SOURCE
    _PANEL = df.copy()
    _PANEL["date"] = pd.to_datetime(_PANEL["date"])
    _PANEL_SOURCE = source
    _set_panel_load_diagnostics(None, None)


def _discover_default_panel_path() -> tuple[Path | None, str | None, str | None]:
    model_dir = Path("data/models")
    for report_path in sorted(
        model_dir.glob("risk_model_vnindex*.json"), key=lambda p: p.stat().st_mtime, reverse=True
    ):
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        panel_path = report.get("panel_path")
        if isinstance(panel_path, str):
            candidate = Path(panel_path)
            if candidate.exists():
                return candidate, None, None
            # Absolute path from another machine/container — try by filename in data/cache/
            local_candidate = Path("data/cache") / candidate.name
            if local_candidate.exists():
                logger.info("Resolved panel by filename: %s", local_candidate)
                return local_candidate, None, None
            return (
                None,
                f"Model report '{report_path.name}' đang tham chiếu tới panel không còn tồn tại: {candidate}",
                "Chạy lại `risk-fetch-universe --start 2015-01-01 --end 2026-03-29 --out ./data/cache` "
                "hoặc khôi phục file parquet rồi restart backend.",
            )
    cache_dir = Path("data/cache")
    candidates = sorted(cache_dir.glob("panel_*.parquet"), key=lambda p: p.stat().st_mtime, reverse=True)
    if candidates:
        return candidates[0], None, None

    universe_manifests = sorted(
        cache_dir.glob("market_universe_manifest_*.json"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if universe_manifests:
        latest_manifest = universe_manifests[0]
        try:
            manifest = json.loads(latest_manifest.read_text(encoding="utf-8"))
        except Exception:
            manifest = {}
        missing_panel_path = manifest.get("training_panel_parquet")
        if isinstance(missing_panel_path, str):
            return (
                None,
                f"Manifest '{latest_manifest.name}' cho thấy panel đã từng được tạo nhưng file hiện bị thiếu: {missing_panel_path}",
                "Tái tạo lại cache bằng `risk-fetch-universe ... --out ./data/cache` hoặc nạp panel thủ công qua "
                "`/admin/load-panel`.",
            )

    return (
        None,
        "Không tìm thấy training panel trong `data/cache` và cũng không có model report trỏ tới file hợp lệ.",
        "Sinh lại panel bằng pipeline ingest/fetch rồi restart backend.",
    )


def autoload_default_panel() -> bool:
    candidate, error, hint = _discover_default_panel_path()
    if candidate is None:
        _set_panel_load_diagnostics(error, hint)
        return False
    try:
        panel = pd.read_parquet(candidate)
    except Exception as exc:
        _set_panel_load_diagnostics(
            f"Đọc panel thất bại tại '{candidate}': {exc}",
            "Kiểm tra file parquet có bị hỏng không hoặc tạo lại panel mới.",
        )
        return False
    set_panel_from_frame(panel, source=str(candidate))
    return True


def panel_status() -> dict[str, object]:
    if _PANEL is None or _PANEL.empty:
        return {
            "loaded": False,
            "rows": 0,
            "start_date": None,
            "end_date": None,
            "source": None,
            "error": _PANEL_LOAD_ERROR,
            "hint": _PANEL_LOAD_HINT,
        }
    panel = _PANEL.copy()
    panel["date"] = pd.to_datetime(panel["date"])
    return {
        "loaded": True,
        "rows": int(len(panel)),
        "start_date": panel["date"].min().date().isoformat(),
        "end_date": panel["date"].max().date().isoformat(),
        "source": _PANEL_SOURCE,
        "error": None,
        "hint": None,
    }


def panel_date_range() -> tuple[str | None, str | None]:
    if _PANEL is None or _PANEL.empty:
        return None, None
    panel = _PANEL.copy()
    panel["date"] = pd.to_datetime(panel["date"])
    start = panel["date"].min()
    end = panel["date"].max()
    return start.date().isoformat(), end.date().isoformat()


@app.on_event("startup")
def startup_autoload_panel() -> None:
    if _PANEL is None:
        loaded = autoload_default_panel()
        logger.info("Panel autoload: %s (source=%s)", "OK" if loaded else "FAIL", _PANEL_SOURCE)


@app.get("/health", tags=["System"])
def health() -> dict:
    panel_ok = _PANEL is not None and not _PANEL.empty
    model_ok = Path("data/models/latest_model.pkl").exists()
    status = "ok" if panel_ok else "degraded"
    return {
        "status": status,
        "checks": {
            "panel_loaded": panel_ok,
            "model_available": model_ok,
        },
    }


@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
def dashboard() -> str:
    return _dashboard_html_path().read_text(encoding="utf-8")


@app.get("/dashboard/state", tags=["Dashboard"])
def dashboard_state() -> dict[str, object]:
    return panel_status()

@app.get("/dashboard/history", tags=["Dashboard"])
def dashboard_history(limit: int = 150):
    panel = get_panel()
    if panel.empty:
        return {"data": []}
    
    df = panel.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    
    trained_model, _ = _get_cached_trained_model(df, df["date"].max(), "skhgb-v4-hybrid", None, None, None)
    
    # Generate features for the batch (we only need the last 'limit' valid rows, but we need history for rolling)
    feat_df = prepare_features(df, vn30_panel=None)
    feat_df = feat_df.tail(limit)
    
    results = []
    for _, row in feat_df.iterrows():
        try:
            # XGBoost allows NaNs
            _, _, _, _, score = predict_horizons(trained_model, row)
            results.append({
                "time": row["date"].strftime("%Y-%m-%d"),
                "value": float(row["vn_index"]),
                "risk_score": float(score)
            })
        except Exception:
            continue
            
    return {"data": results}


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

@app.get("/dashboard/live", tags=["Dashboard"])
def dashboard_live():
    panel = get_panel()
    if panel.empty:
        return {}
        
    df = panel.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    
    # Lấy giá trị trực tiếp từ thị trường (DNSE)
    last_row = df.iloc[-1].copy()
    base_price = float(last_row["vn_index"])
    current_vn_index, market_time = _get_live_vnindex_dnse(base_price)
    
    last_row["vn_index"] = current_vn_index
    
    # Cập nhật thời gian thực vào df
    last_row["date"] = pd.to_datetime(market_time, unit='s')
    
    df = pd.concat([df, pd.DataFrame([last_row])], ignore_index=True)
    
    trained_model, _ = _get_cached_trained_model(df, df["date"].max(), "skhgb-v4-hybrid", None, None, None)
    feat_df = prepare_features(df, vn30_panel=None)
    
    pred_row = feat_df.iloc[-1]
    _, _, _, _, score = predict_horizons(trained_model, pred_row)
    
    # ADVANCED METRICS (HMM + GARCH + BL-Allocation)
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
        "cash_pct": alloc["cash_pct"]
    }



@app.post("/admin/load-panel", tags=["Admin"])
def load_panel(payload: dict) -> dict[str, str]:
    """Nạp panel từ JSON records (test/demo)."""
    panel = pd.DataFrame(payload["records"])
    set_panel_from_frame(panel, source="admin/load-panel")
    return {"ok": "true", "rows": str(len(_PANEL) if _PANEL is not None else 0)}


class EODRequest(BaseModel):
    as_of: date
    run_id: str | None = None


@app.post("/eod/run", tags=["Quant"])
def eod_run(req: EODRequest):
    manifest = run_eod_narrative(get_panel(), req.as_of, run_id=req.run_id)
    return manifest.model_dump(mode="json")


class ScenarioRequest(BaseModel):
    as_of: date
    usd_vnd_rate: float | None = None
    sbv_interest_rate_pct: float | None = None


@app.post("/scenario/rerun", tags=["Quant"])
def scenario_rerun(req: ScenarioRequest):
    panel = get_panel()
    try:
        q = rerun_with_macro_override(
            panel,
            req.as_of,
            usd_vnd_rate=req.usd_vnd_rate,
            sbv_interest_rate_pct=req.sbv_interest_rate_pct,
        )
    except ValueError as exc:
        start_date, end_date = panel_date_range()
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Scenario rerun failed",
                "error": str(exc),
                "hint": f"Chọn ngày có trong panel, hiện khả dụng từ {start_date} đến {end_date}.",
            },
        ) from exc
    return q.model_dump(mode="json")


@app.get("/research/model-report", tags=["Quant"])
def research_model_report():
    report = build_model_research_report("data/models")
    return {
        "created_at": report.created_at,
        "model_dir": report.model_dir,
        "summary": report.summary,
    }


class ChatRequest(BaseModel):
    as_of: date
    message: str = Field(..., min_length=1)


@app.post("/chat", tags=["Chat"])
def chat(req: ChatRequest):
    """Multi-agent chat — LangGraph pipeline with real tools."""
    return run_chat(req.message)


@app.get("/financials/status", tags=["Financials"])
def financials_status() -> dict[str, object]:
    return {
        "provider": "vnstock-live",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "notes": [
            "Provider BCTC mặc định hiện dùng vnstock 3.x với luồng live fetch.",
            "Môi trường đã nâng lên Python 3.10+ để tương thích provider mới.",
            "Có thể import cache JSON chuẩn hóa nếu provider live thất bại.",
        ],
    }


@app.get("/financials/{ticker}/analysis", tags=["Financials"])
def financial_analysis(ticker: str, refresh: bool = False):
    try:
        dataset = get_financial_dataset(ticker, refresh=refresh)
    except FinancialDataError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "message": exc.message,
                "error": exc.notes[0] if exc.notes else None,
                "hint": exc.hint,
                "notes": exc.notes,
            },
        ) from exc

    return analyze_financial_dataset(dataset).model_dump(mode="json")


@app.post("/financials/import", tags=["Financials"])
def financial_import(req: FinancialImportRequest):
    path = import_financial_dataset(req.dataset)
    analysis = analyze_financial_dataset(req.dataset)
    return {
        "ok": True,
        "path": str(path),
        "ticker": req.dataset.ticker,
        "periods": len(req.dataset.periods),
        "analysis": analysis.model_dump(mode="json"),
    }

@app.get("/dashboard/money-flow", tags=["Dashboard"])
def dashboard_money_flow():
    """
    Cung cấp số liệu Dòng tiền chuyên sâu (Money Flow).
    Mocked realistic data for UI / Agent Treemap analysis.
    """
    return {
        "foreign_net_val": -450.5,
        "sectors": [
            {"name": "Ngân hàng", "flow": 520.4, "weight": 0.35},
            {"name": "Bất động sản", "flow": -310.2, "weight": 0.20},
            {"name": "Chứng khoán", "flow": 150.8, "weight": 0.15},
            {"name": "Thép", "flow": -85.5, "weight": 0.10},
            {"name": "Bán lẻ", "flow": 45.2, "weight": 0.08},
            {"name": "Dầu khí", "flow": -12.4, "weight": 0.07},
            {"name": "Công nghệ", "flow": 210.6, "weight": 0.05}
        ]
    }
