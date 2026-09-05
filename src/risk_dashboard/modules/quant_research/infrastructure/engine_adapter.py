"""Canonical engine adapter for Quantitative Finance Research Agent."""
from __future__ import annotations

from datetime import date, datetime, timezone
import logging
from pathlib import Path
from typing import Literal

import pandas as pd

from risk_dashboard.engines.quant.eod_pipeline import run_quant_eod
from risk_dashboard.engines.quant.research_report import build_model_research_report
from risk_dashboard.engines.quant.scenario import rerun_with_macro_override
from risk_dashboard.platform.runtime.panel_store import (
    PanelUnavailableError,
    get_panel,
)
from risk_dashboard.schemas.snapshots import QuantEngineOutput
from risk_dashboard.modules.quant_research.domain.errors import QuantAdapterError
from risk_dashboard.modules.quant_research.infrastructure.adapter_helpers import (
    build_eod_source_refs,
    build_model_report_source_refs,
    build_scenario_source_refs,
    check_date_in_panel,
    sanitize_floats,
    wrap_scenario_error,
)
from risk_dashboard.modules.quant_research.schemas.tools import QuantToolResultV1

logger = logging.getLogger(__name__)

__all__ = ["QuantAdapterError", "QuantEngineAdapter"]


class QuantEngineAdapter:
    """Read-only adapter wrapping canonical quantitative finance engines."""

    def __init__(
        self,
        *,
        models_dir: str | Path = "data/models",
        panel_override: pd.DataFrame | None = None,
    ) -> None:
        self._models_dir = Path(models_dir)
        self._panel_override = panel_override

    def _load_panel(self) -> pd.DataFrame:
        if self._panel_override is not None:
            return self._panel_override
        try:
            return get_panel()
        except PanelUnavailableError as exc:
            logger.warning("Panel is unavailable: %s", exc)
            raise QuantAdapterError(
                "panel_unavailable",
                "Panel data is currently unavailable.",
                hint="Dữ liệu thị trường chưa sẵn sàng, vui lòng thử lại sau.",
                cause=exc,
            ) from exc

    async def run_eod_analysis(
        self, *, as_of: date, run_id: str | None = None
    ) -> QuantToolResultV1:
        """Run canonical EOD quantitative analysis."""
        panel = self._load_panel()
        check_date_in_panel(as_of, panel)

        try:
            output: QuantEngineOutput = run_quant_eod(
                panel,
                as_of,
                run_id=run_id,
                benchmark_dir=self._models_dir,
            )
        except QuantAdapterError:
            raise
        except Exception as exc:
            logger.error("Canonical run_quant_eod failed: %s", exc, exc_info=True)
            raise QuantAdapterError(
                "engine_failure",
                f"EOD quantitative calculation failed: {exc}",
                cause=exc,
            ) from exc

        now = datetime.now(timezone.utc)
        source_refs = build_eod_source_refs(as_of, output.model_version, output.as_of, now)

        return QuantToolResultV1(
            tool_name="quant.eod_analysis.v1",
            status="ok",
            payload=output.model_dump(mode="json"),
            source_refs=source_refs,
            warnings=(),
            generated_at=now,
        )

    async def compare_macro_scenario(
        self,
        *,
        as_of: date,
        usd_vnd_rate: float | None = None,
        sbv_interest_rate_pct: float | None = None,
    ) -> QuantToolResultV1:
        """Run canonical macro scenario comparison."""
        panel = self._load_panel()
        check_date_in_panel(as_of, panel)

        try:
            output: QuantEngineOutput = rerun_with_macro_override(
                panel,
                as_of,
                usd_vnd_rate=usd_vnd_rate,
                sbv_interest_rate_pct=sbv_interest_rate_pct,
                benchmark_dir=self._models_dir,
            )
        except ValueError as exc:
            raise wrap_scenario_error(exc) from exc
        except QuantAdapterError:
            raise
        except Exception as exc:
            logger.error("Canonical rerun_with_macro_override failed: %s", exc, exc_info=True)
            raise QuantAdapterError(
                "engine_failure",
                f"Macro scenario calculation failed: {exc}",
                cause=exc,
            ) from exc

        now = datetime.now(timezone.utc)
        source_refs = build_scenario_source_refs(as_of, output.model_version, output.as_of, now)

        return QuantToolResultV1(
            tool_name="quant.scenario_compare.v1",
            status="ok",
            payload=output.model_dump(mode="json"),
            source_refs=source_refs,
            warnings=(),
            generated_at=now,
        )

    async def get_model_research_report(
        self, *, model_ref: Literal["latest"] = "latest"
    ) -> QuantToolResultV1:
        """Build model research benchmark report."""
        if model_ref != "latest":
            raise QuantAdapterError(
                "invalid_input",
                f"Invalid model_ref '{model_ref}'. Only 'latest' is permitted; arbitrary paths are forbidden.",
                hint="Chỉ chấp nhận model_ref='latest'.",
            )

        try:
            report = build_model_research_report(self._models_dir)
        except FileNotFoundError as exc:
            raise QuantAdapterError(
                "model_unavailable",
                f"Model report not found in directory: {exc}",
                hint="Mô hình chưa được huấn luyện hoặc không tìm thấy file benchmark.",
                cause=exc,
            ) from exc
        except Exception as exc:
            logger.error("build_model_research_report failed: %s", exc, exc_info=True)
            raise QuantAdapterError(
                "engine_failure",
                f"Failed to generate model research report: {exc}",
                cause=exc,
            ) from exc

        now = datetime.now(timezone.utc)
        clean_summary = {
            k: sanitize_floats(v)
            for k, v in report.summary.items()
            if not k.endswith("_path")
        }
        payload = {
            "created_at": report.created_at,
            "summary": clean_summary,
            "evidence_status": "available",
        }
        model_version = str(report.summary.get("model_version", "latest"))
        source_refs = build_model_report_source_refs(model_version, now)

        return QuantToolResultV1(
            tool_name="quant.model_report.v1",
            status="ok",
            payload=payload,
            source_refs=source_refs,
            warnings=(),
            generated_at=now,
        )
