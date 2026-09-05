"""Helpers for quant engine adapter operations."""
from __future__ import annotations

from datetime import date, datetime, timezone
import math
from typing import Any

import pandas as pd

from risk_dashboard.modules.quant_research.domain.errors import QuantAdapterError
from risk_dashboard.modules.quant_research.schemas.tools import QuantSourceRefV1
from risk_dashboard.platform.runtime.panel_store import panel_date_range


def check_date_in_panel(as_of: date, panel: pd.DataFrame) -> None:
    """Verify that as_of date is present in panel dataframe."""
    if "date" in panel.columns:
        panel_dates = pd.to_datetime(panel["date"]).dt.date
        if as_of not in set(panel_dates):
            try:
                start_date, end_date = panel_date_range()
            except Exception:
                start_date = panel_dates.min() if not panel_dates.empty else None
                end_date = panel_dates.max() if not panel_dates.empty else None
            raise QuantAdapterError(
                "date_out_of_range",
                f"Selected date {as_of} is not present in available panel data.",
                hint=f"Chọn ngày có trong panel, hiện khả dụng từ {start_date} đến {end_date}.",
            )


def wrap_scenario_error(exc: ValueError) -> QuantAdapterError:
    """Wrap scenario ValueError with date range hint."""
    try:
        start_date, end_date = panel_date_range()
    except Exception:
        start_date, end_date = None, None
    return QuantAdapterError(
        "date_out_of_range",
        f"Scenario rerun failed: {exc}",
        hint=f"Chọn ngày có trong panel, hiện khả dụng từ {start_date} đến {end_date}.",
        cause=exc,
    )


def sanitize_floats(obj: Any) -> Any:
    """Recursively replace NaN and Inf with None."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: sanitize_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_floats(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(sanitize_floats(v) for v in obj)
    return obj


def build_eod_source_refs(
    as_of: date,
    model_version: str | None,
    model_as_of: Any,
    now: datetime,
) -> tuple[QuantSourceRefV1, ...]:
    """Build source references for EOD analysis."""
    as_of_dt = datetime.combine(as_of, datetime.min.time(), tzinfo=timezone.utc)
    return (
        QuantSourceRefV1(
            source_id="panel_eod_vnindex",
            source_type="panel",
            version="panel_v1",
            as_of=as_of_dt,
        ),
        QuantSourceRefV1(
            source_id="model_risk_xgb",
            source_type="model",
            version=model_version or "skhgb-v4-hybrid",
            as_of=model_as_of,
        ),
        QuantSourceRefV1(
            source_id="engine_quant_eod",
            source_type="engine",
            version="1.0.0",
            as_of=now,
        ),
    )


def build_scenario_source_refs(
    as_of: date,
    model_version: str | None,
    model_as_of: Any,
    now: datetime,
) -> tuple[QuantSourceRefV1, ...]:
    """Build source references for scenario comparison."""
    as_of_dt = datetime.combine(as_of, datetime.min.time(), tzinfo=timezone.utc)
    return (
        QuantSourceRefV1(
            source_id="panel_scenario_vnindex",
            source_type="panel",
            version="panel_v1",
            as_of=as_of_dt,
        ),
        QuantSourceRefV1(
            source_id="model_risk_xgb_scenario",
            source_type="model",
            version=model_version or "skhgb-v4-hybrid-scenario",
            as_of=model_as_of,
        ),
        QuantSourceRefV1(
            source_id="engine_quant_scenario",
            source_type="engine",
            version="1.0.0",
            as_of=now,
        ),
    )


def build_model_report_source_refs(model_version: str, now: datetime) -> tuple[QuantSourceRefV1, ...]:
    """Build source references for model report."""
    return (
        QuantSourceRefV1(
            source_id="model_benchmark_data",
            source_type="benchmark",
            version="1.0.0",
            as_of=now,
        ),
        QuantSourceRefV1(
            source_id="model_artifact_report",
            source_type="model",
            version=model_version,
            as_of=now,
        ),
    )
