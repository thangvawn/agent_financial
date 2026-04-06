from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from risk_dashboard.quant.eod_pipeline import run_quant_eod
from risk_dashboard.schemas.snapshots import QuantEngineOutput


def rerun_with_macro_override(
    panel: pd.DataFrame,
    as_of: date,
    *,
    vn30_panel: pd.DataFrame | None = None,
    usd_vnd_rate: float | None = None,
    sbv_interest_rate_pct: float | None = None,
    usd_vnd_1m_change_pct: float | None = None,
    run_id: str | None = None,
    benchmark_dir: str | Path | None = "data/models",
) -> QuantEngineOutput:
    """What-if: chỉnh macro trên dòng as_of rồi chạy lại quant."""
    df = panel.copy()
    df["date"] = pd.to_datetime(df["date"])
    mask = df["date"] == pd.Timestamp(as_of)
    if not mask.any():
        raise ValueError("as_of not in panel")
    idx = df.index[mask][0]
    if usd_vnd_rate is not None:
        df.at[idx, "usd_vnd_rate"] = usd_vnd_rate
    if sbv_interest_rate_pct is not None:
        df.at[idx, "sbv_interest_rate_pct"] = sbv_interest_rate_pct
    if usd_vnd_1m_change_pct is not None:
        df.at[idx, "usd_vnd_1m_change_pct"] = usd_vnd_1m_change_pct
    return run_quant_eod(
        df,
        as_of,
        run_id=run_id,
        model_version="skhgb-v4-hybrid-scenario",
        vn30_panel=vn30_panel,
        benchmark_dir=benchmark_dir,
    )
