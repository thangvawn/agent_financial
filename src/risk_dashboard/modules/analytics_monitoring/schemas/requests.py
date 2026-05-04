from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyticsEventItemRequest(BaseModel):
    event_name: str = Field(..., min_length=3, max_length=100)
    event_category: str = Field(..., pattern="^(product|ops|trust_safety|admin)$")
    schema_version: int = Field(default=1, ge=1)
    timestamp: str
    module: str = Field(..., min_length=2, max_length=80)
    surface: str = Field(..., min_length=2, max_length=80)
    user_id: str | None = None
    session_id: str | None = None
    persona_segment: str | None = None
    route: str | None = None
    locale: str | None = None
    device_type: str | None = None
    source_surface: str | None = None
    target_surface: str | None = None
    properties: dict[str, object] = Field(default_factory=dict)


class AnalyticsIngestRequest(BaseModel):
    events: list[AnalyticsEventItemRequest] = Field(..., min_length=1, max_length=250)


class KpiRollupRequest(BaseModel):
    window_grain: str = Field(default="day", pattern="^(hour|day|week)$")


class OpsSnapshotRequest(BaseModel):
    window_hours: int = Field(default=24, ge=1, le=168)


class AlertEvaluationRequest(BaseModel):
    force_reopen: bool = False
