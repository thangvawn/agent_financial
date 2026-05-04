from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from risk_dashboard.agents.graph import run_eod_narrative
from risk_dashboard.platform.runtime.panel_store import PanelUnavailableError, get_panel, panel_date_range
from risk_dashboard.quant.research_report import build_model_research_report
from risk_dashboard.quant.scenario import rerun_with_macro_override

router = APIRouter(tags=["Quant"])


class EODRequest(BaseModel):
    as_of: date
    run_id: str | None = None


class ScenarioRequest(BaseModel):
    as_of: date
    usd_vnd_rate: float | None = None
    sbv_interest_rate_pct: float | None = None


@router.post("/eod/run", tags=["Quant"])
def eod_run(req: EODRequest):
    try:
        panel = get_panel()
    except PanelUnavailableError as exc:
        raise HTTPException(status_code=503, detail=exc.detail) from exc
    manifest = run_eod_narrative(panel, req.as_of, run_id=req.run_id)
    return manifest.model_dump(mode="json")


@router.post("/scenario/rerun", tags=["Quant"])
def scenario_rerun(req: ScenarioRequest):
    try:
        panel = get_panel()
    except PanelUnavailableError as exc:
        raise HTTPException(status_code=503, detail=exc.detail) from exc

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


@router.get("/research/model-report", tags=["Quant"])
def research_model_report():
    report = build_model_research_report("data/models")
    return {
        "created_at": report.created_at,
        "model_dir": report.model_dir,
        "summary": report.summary,
    }
