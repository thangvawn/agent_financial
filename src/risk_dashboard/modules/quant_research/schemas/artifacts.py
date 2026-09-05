"""Artifact schemas for quant_research module."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from risk_dashboard.modules.quant_research.schemas.tools import QuantSourceRefV1


class QuantResearchArtifactV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0.0"] = "1.0.0"
    artifact_type: Literal["quant_research"] = "quant_research"
    run_id: str
    operation: Literal["eod_analysis", "scenario_compare", "model_report"]
    headline: str
    findings: tuple[str, ...]
    metrics: dict[str, float | int | str | None]
    source_refs: tuple[QuantSourceRefV1, ...]
    assumptions: tuple[str, ...] = ()
    limitations: tuple[str, ...]
    review_status: Literal["verified", "blocked"]
    generated_at: datetime

