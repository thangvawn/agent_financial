from __future__ import annotations

from pydantic import BaseModel


class AnalyticsIngestResponse(BaseModel):
    accepted: int
    rejected: int


class AnalyticsStatusResponse(BaseModel):
    enabled: bool
    total_events: int
    total_kpi_snapshots: int
    total_ops_snapshots: int
    open_alerts: int


class AnalyticsEventResponse(BaseModel):
    event_id: str
    event_name: str
    event_category: str
    timestamp: str
    module: str
    surface: str
    user_id: str | None = None
    session_id: str | None = None
    persona_segment: str | None = None
    route: str | None = None
    source_surface: str | None = None
    target_surface: str | None = None
    properties: dict[str, object] | None = None


class AnalyticsKpiSnapshotResponse(BaseModel):
    snapshot_id: str
    kpi_name: str
    window_grain: str
    window_start: str
    window_end: str
    value: float
    segment_key: str | None = None
    segment_value: str | None = None
    meta: dict[str, object] | None = None
    created_at: str


class OpsMetricSnapshotResponse(BaseModel):
    snapshot_id: str
    metric_name: str
    metric_group: str
    surface: str | None = None
    status: str
    value: float
    unit: str
    captured_at: str
    meta: dict[str, object] | None = None


class OpsAlertEventResponse(BaseModel):
    alert_id: str
    rule_name: str
    severity_tier: str
    surface: str | None = None
    status: str
    summary: str
    details: dict[str, object] | None = None
    triggered_at: str
    resolved_at: str | None = None


class AnalyticsDashboardMetricResponse(BaseModel):
    key: str
    label: str
    value: float
    unit: str
    status: str
    context: str | None = None


class AnalyticsDashboardModuleResponse(BaseModel):
    module: str
    event_count: int
    unique_sessions: int
    last_event_at: str | None = None


class AnalyticsDashboardResponse(BaseModel):
    dashboard_id: str
    title: str
    window_grain: str
    summary_metrics: list[AnalyticsDashboardMetricResponse]
    module_activity: list[AnalyticsDashboardModuleResponse]
    recent_events: list[AnalyticsEventResponse]
    open_alerts: list[OpsAlertEventResponse]
