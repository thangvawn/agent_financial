from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class AnalyticsEvent:
    event_id: str
    event_name: str
    event_category: str
    schema_version: int
    timestamp: str
    module: str
    surface: str
    properties_json: str
    user_id: str | None = None
    session_id: str | None = None
    persona_segment: str | None = None
    route: str | None = None
    locale: str | None = None
    device_type: str | None = None
    source_surface: str | None = None
    target_surface: str | None = None


@dataclass(frozen=True)
class AnalyticsKpiSnapshot:
    snapshot_id: str
    kpi_name: str
    window_grain: str
    window_start: str
    window_end: str
    value: float
    created_at: str = field(default_factory=utc_now_iso)
    segment_key: str | None = None
    segment_value: str | None = None
    meta_json: str | None = None


@dataclass(frozen=True)
class OpsMetricSnapshot:
    snapshot_id: str
    metric_name: str
    metric_group: str
    status: str
    value: float
    unit: str
    captured_at: str
    surface: str | None = None
    meta_json: str | None = None


@dataclass(frozen=True)
class OpsAlertEvent:
    alert_id: str
    rule_name: str
    severity_tier: str
    status: str
    summary: str
    triggered_at: str
    surface: str | None = None
    details_json: str | None = None
    resolved_at: str | None = None
