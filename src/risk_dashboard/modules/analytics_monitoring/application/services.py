from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta, timezone

from risk_dashboard.modules.analytics_monitoring.domain.alert_rules import ALERT_RULES
from risk_dashboard.modules.analytics_monitoring.domain.events import (
    AnalyticsEvent,
    AnalyticsKpiSnapshot,
    OpsAlertEvent,
    OpsMetricSnapshot,
    utc_now_iso,
)
from risk_dashboard.modules.analytics_monitoring.domain.kpi_definitions import KPI_EVENT_MAP, SUPPORTED_WINDOW_GRAINS
from risk_dashboard.modules.analytics_monitoring.infrastructure.repositories.sqlite import (
    SqliteAnalyticsMonitoringRepository,
    new_analytics_event_id,
    new_analytics_snapshot_id,
    new_ops_alert_id,
)
from risk_dashboard.modules.analytics_monitoring.schemas.requests import (
    AlertEvaluationRequest,
    AnalyticsIngestRequest,
    KpiRollupRequest,
    OpsSnapshotRequest,
)
from risk_dashboard.modules.analytics_monitoring.schemas.responses import (
    AnalyticsDashboardMetricResponse,
    AnalyticsDashboardModuleResponse,
    AnalyticsDashboardResponse,
    AnalyticsEventResponse,
    AnalyticsIngestResponse,
    AnalyticsKpiSnapshotResponse,
    AnalyticsStatusResponse,
    OpsAlertEventResponse,
    OpsMetricSnapshotResponse,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _window_start(now: datetime, window_grain: str) -> datetime:
    if window_grain == "hour":
        return now - timedelta(hours=1)
    if window_grain == "week":
        return now - timedelta(days=7)
    return now - timedelta(days=1)


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * pct))
    return float(ordered[index])


class IngestAnalyticsEvents:
    def __init__(self, repo: SqliteAnalyticsMonitoringRepository) -> None:
        self.repo = repo

    def execute(self, req: AnalyticsIngestRequest) -> AnalyticsIngestResponse:
        events = [
            AnalyticsEvent(
                event_id=new_analytics_event_id(),
                event_name=item.event_name,
                event_category=item.event_category,
                schema_version=item.schema_version,
                timestamp=item.timestamp,
                module=item.module,
                surface=item.surface,
                user_id=item.user_id,
                session_id=item.session_id,
                persona_segment=item.persona_segment,
                route=item.route,
                locale=item.locale,
                device_type=item.device_type,
                source_surface=item.source_surface,
                target_surface=item.target_surface,
                properties_json=json.dumps(item.properties, ensure_ascii=False),
            )
            for item in req.events
        ]
        self.repo.save_events(events)
        return AnalyticsIngestResponse(accepted=len(events), rejected=0)


class GetAnalyticsStatus:
    def __init__(self, repo: SqliteAnalyticsMonitoringRepository) -> None:
        self.repo = repo

    def execute(self, *, enabled: bool) -> AnalyticsStatusResponse:
        return AnalyticsStatusResponse(enabled=enabled, **self.repo.overview())


class RunKpiRollups:
    def __init__(self, repo: SqliteAnalyticsMonitoringRepository) -> None:
        self.repo = repo

    def execute(self, req: KpiRollupRequest) -> list[AnalyticsKpiSnapshotResponse]:
        if req.window_grain not in SUPPORTED_WINDOW_GRAINS:
            raise ValueError("Unsupported window grain.")
        now = _utc_now()
        start = _window_start(now, req.window_grain)
        events = self.repo.list_events(window_start=start.isoformat(), window_end=now.isoformat())
        counts = Counter(item.event_name for item in events)
        snapshots: list[AnalyticsKpiSnapshot] = []

        for kpi_name, event_names in KPI_EVENT_MAP:
            value = float(sum(counts.get(name, 0) for name in event_names))
            snapshots.append(
                AnalyticsKpiSnapshot(
                    snapshot_id=new_analytics_snapshot_id(),
                    kpi_name=kpi_name,
                    window_grain=req.window_grain,
                    window_start=start.isoformat(),
                    window_end=now.isoformat(),
                    value=value,
                    meta_json=json.dumps({"event_names": list(event_names)}, ensure_ascii=False),
                )
            )

        started = counts.get("onboarding_started", 0)
        completed = counts.get("onboarding_completed", 0)
        onboarding_completion_rate = float(completed / started) if started else 0.0
        snapshots.append(
            AnalyticsKpiSnapshot(
                snapshot_id=new_analytics_snapshot_id(),
                kpi_name="onboarding_completion_rate",
                window_grain=req.window_grain,
                window_start=start.isoformat(),
                window_end=now.isoformat(),
                value=onboarding_completion_rate,
                meta_json=json.dumps({"started": started, "completed": completed}, ensure_ascii=False),
            )
        )

        saved = self.repo.save_kpi_snapshots(snapshots)
        return [_to_kpi_response(item) for item in saved]


class RunOpsSnapshots:
    def __init__(self, repo: SqliteAnalyticsMonitoringRepository) -> None:
        self.repo = repo

    def execute(self, req: OpsSnapshotRequest) -> list[OpsMetricSnapshotResponse]:
        now = _utc_now()
        start = now - timedelta(hours=req.window_hours)
        events = self.repo.list_events(window_start=start.isoformat(), window_end=now.isoformat())
        ops_events = [item for item in events if item.event_category == "ops"]

        api_events = [item for item in ops_events if item.event_name == "ops_api_request_logged"]
        model_events = [item for item in ops_events if item.event_name == "ops_model_call_logged"]
        data_events = [item for item in ops_events if item.event_name == "ops_data_refresh_logged"]

        api_success_count = 0
        api_total_count = len(api_events)
        api_latencies: list[float] = []
        for item in api_events:
            props = json.loads(item.properties_json or "{}")
            if bool(props.get("success", False)):
                api_success_count += 1
            latency = props.get("latency_ms")
            if isinstance(latency, (int, float)):
                api_latencies.append(float(latency))
        api_success_rate = float(api_success_count / api_total_count) if api_total_count else 1.0
        api_error_rate = float(1.0 - api_success_rate) if api_total_count else 0.0
        api_p95_latency = _percentile(api_latencies, 0.95)

        model_success_count = 0
        model_total_count = len(model_events)
        model_latencies: list[float] = []
        for item in model_events:
            props = json.loads(item.properties_json or "{}")
            if bool(props.get("success", False)):
                model_success_count += 1
            latency = props.get("latency_ms")
            if isinstance(latency, (int, float)):
                model_latencies.append(float(latency))
        model_failure_rate = float(1.0 - (model_success_count / model_total_count)) if model_total_count else 0.0
        model_latency_p95 = _percentile(model_latencies, 0.95)

        stale_count = 0
        for item in data_events:
            props = json.loads(item.properties_json or "{}")
            freshness = str(props.get("freshness_status", "")).strip().lower()
            if freshness in {"stale", "unavailable"}:
                stale_count += 1
        stale_insight_rate = float(stale_count / len(data_events)) if data_events else 0.0

        moderation_queue_volume = float(self.repo.count_held_for_review())
        open_trust_incident_count = float(self.repo.count_open_trust_incidents())
        critical_trust_incident_count = float(self.repo.count_open_trust_incidents(severity="critical"))

        captured_at = now.isoformat()
        metrics = [
            OpsMetricSnapshot(
                snapshot_id=new_analytics_snapshot_id(),
                metric_name="api_success_rate",
                metric_group="api_health",
                surface="public_api",
                status="good" if api_success_rate >= 0.95 else "degraded",
                value=api_success_rate,
                unit="ratio",
                captured_at=captured_at,
            ),
            OpsMetricSnapshot(
                snapshot_id=new_analytics_snapshot_id(),
                metric_name="api_error_rate",
                metric_group="api_health",
                surface="public_api",
                status="good" if api_error_rate <= 0.05 else "degraded",
                value=api_error_rate,
                unit="ratio",
                captured_at=captured_at,
            ),
            OpsMetricSnapshot(
                snapshot_id=new_analytics_snapshot_id(),
                metric_name="api_p95_latency_ms",
                metric_group="api_health",
                surface="public_api",
                status="good" if api_p95_latency <= 2000 else "degraded",
                value=api_p95_latency,
                unit="ms",
                captured_at=captured_at,
            ),
            OpsMetricSnapshot(
                snapshot_id=new_analytics_snapshot_id(),
                metric_name="model_latency_p95_ms",
                metric_group="model_health",
                surface="pro_lab",
                status="good" if model_latency_p95 <= 4000 else "degraded",
                value=model_latency_p95,
                unit="ms",
                captured_at=captured_at,
            ),
            OpsMetricSnapshot(
                snapshot_id=new_analytics_snapshot_id(),
                metric_name="model_failure_rate",
                metric_group="model_health",
                surface="pro_lab",
                status="good" if model_failure_rate <= 0.05 else "degraded",
                value=model_failure_rate,
                unit="ratio",
                captured_at=captured_at,
            ),
            OpsMetricSnapshot(
                snapshot_id=new_analytics_snapshot_id(),
                metric_name="stale_insight_rate",
                metric_group="data_freshness",
                surface="insights",
                status="good" if stale_insight_rate <= 0.20 else "degraded",
                value=stale_insight_rate,
                unit="ratio",
                captured_at=captured_at,
            ),
            OpsMetricSnapshot(
                snapshot_id=new_analytics_snapshot_id(),
                metric_name="moderation_queue_volume",
                metric_group="moderation",
                surface="community",
                status="good" if moderation_queue_volume <= 100 else "degraded",
                value=moderation_queue_volume,
                unit="count",
                captured_at=captured_at,
            ),
            OpsMetricSnapshot(
                snapshot_id=new_analytics_snapshot_id(),
                metric_name="open_trust_incident_count",
                metric_group="moderation",
                surface="trust_safety",
                status="good" if open_trust_incident_count == 0 else "degraded",
                value=open_trust_incident_count,
                unit="count",
                captured_at=captured_at,
            ),
            OpsMetricSnapshot(
                snapshot_id=new_analytics_snapshot_id(),
                metric_name="critical_trust_incident_count",
                metric_group="moderation",
                surface="trust_safety",
                status="good" if critical_trust_incident_count == 0 else "degraded",
                value=critical_trust_incident_count,
                unit="count",
                captured_at=captured_at,
            ),
        ]
        saved = self.repo.save_ops_metric_snapshots(metrics)
        return [_to_ops_metric_response(item) for item in saved]


class EvaluateAlerts:
    def __init__(self, repo: SqliteAnalyticsMonitoringRepository) -> None:
        self.repo = repo

    def execute(self, req: AlertEvaluationRequest) -> list[OpsAlertEventResponse]:
        items: list[OpsAlertEvent] = []
        now = utc_now_iso()
        for rule in ALERT_RULES:
            latest = self.repo.get_latest_ops_metric(metric_name=str(rule["metric_name"]))
            if latest is None:
                continue
            triggered = float(latest.value) > float(rule["threshold"]) if rule["comparison"] == "gt" else False
            existing = self.repo.get_open_alert(rule_name=str(rule["rule_name"]), surface=str(rule["surface"]))
            if triggered:
                if existing is None or req.force_reopen:
                    items.append(
                        self.repo.save_alert(
                            OpsAlertEvent(
                                alert_id=new_ops_alert_id(),
                                rule_name=str(rule["rule_name"]),
                                severity_tier=str(rule["severity_tier"]),
                                surface=str(rule["surface"]),
                                status="open",
                                summary=str(rule["summary"]),
                                details_json=json.dumps(
                                    {"metric_name": latest.metric_name, "metric_value": latest.value},
                                    ensure_ascii=False,
                                ),
                                triggered_at=now,
                            )
                        )
                    )
            elif existing is not None:
                resolved = self.repo.resolve_open_alert(rule_name=str(rule["rule_name"]), surface=str(rule["surface"]))
                if resolved is not None:
                    items.append(resolved)
        return [_to_alert_response(item) for item in items]


class ListKpiSnapshots:
    def __init__(self, repo: SqliteAnalyticsMonitoringRepository) -> None:
        self.repo = repo

    def execute(self, *, kpi_name: str | None = None, window_grain: str | None = None) -> list[AnalyticsKpiSnapshotResponse]:
        return [
            _to_kpi_response(item)
            for item in self.repo.list_kpi_snapshots(kpi_name=kpi_name, window_grain=window_grain)
        ]


class ListOpsMetrics:
    def __init__(self, repo: SqliteAnalyticsMonitoringRepository) -> None:
        self.repo = repo

    def execute(self, *, metric_group: str | None = None) -> list[OpsMetricSnapshotResponse]:
        return [_to_ops_metric_response(item) for item in self.repo.list_ops_metric_snapshots(metric_group=metric_group)]


class ListAlerts:
    def __init__(self, repo: SqliteAnalyticsMonitoringRepository) -> None:
        self.repo = repo

    def execute(self, *, status: str | None = None) -> list[OpsAlertEventResponse]:
        return [_to_alert_response(item) for item in self.repo.list_alerts(status=status)]


class ListAnalyticsEvents:
    def __init__(self, repo: SqliteAnalyticsMonitoringRepository) -> None:
        self.repo = repo

    def execute(
        self,
        *,
        event_category: str | None = None,
        module: str | None = None,
        surface: str | None = None,
        event_name: str | None = None,
        search: str | None = None,
        limit: int = 100,
    ) -> list[AnalyticsEventResponse]:
        return [
            _to_event_response(item)
            for item in self.repo.list_events(
                event_category=event_category,
                module=module,
                surface=surface,
                event_name=event_name,
                search=search,
                limit=limit,
            )
        ]


class GetProductDashboard:
    def __init__(self, repo: SqliteAnalyticsMonitoringRepository) -> None:
        self.repo = repo

    def execute(self, *, window_grain: str = "day") -> AnalyticsDashboardResponse:
        latest_kpis = _latest_kpi_map(self.repo, window_grain=window_grain)
        recent_events = self.repo.list_events(event_category="product", limit=50)
        return AnalyticsDashboardResponse(
            dashboard_id="product",
            title="Product Analytics",
            window_grain=window_grain,
            summary_metrics=[
                _dashboard_metric("onboarding_completion_rate", "Onboarding completion", latest_kpis, unit="ratio", status_good_threshold=0.6),
                _dashboard_metric("financial_health_completion_count", "Health completions", latest_kpis, unit="count"),
                _dashboard_metric("goal_created_count", "Goals created", latest_kpis, unit="count"),
                _dashboard_metric("learning_lesson_completed_count", "Lessons completed", latest_kpis, unit="count"),
                _dashboard_metric("guided_market_context_view_count", "Guided market views", latest_kpis, unit="count"),
                _dashboard_metric("insight_open_count", "Insight opens", latest_kpis, unit="count"),
                _dashboard_metric("community_join_count", "Community joins", latest_kpis, unit="count"),
                _dashboard_metric("pro_experiment_run_count", "Pro experiment runs", latest_kpis, unit="count"),
            ],
            module_activity=_module_activity(recent_events),
            recent_events=[_to_event_response(item) for item in recent_events[:25]],
            open_alerts=[_to_alert_response(item) for item in self.repo.list_alerts(status="open", limit=10)],
        )


class GetTrustDashboard:
    def __init__(self, repo: SqliteAnalyticsMonitoringRepository) -> None:
        self.repo = repo

    def execute(self) -> AnalyticsDashboardResponse:
        latest_ops = _latest_ops_map(self.repo)
        recent_ops_events = self.repo.list_events(event_category="ops", limit=80)
        recent_trust_events = [
            item
            for item in self.repo.list_events(limit=120)
            if item.event_category == "ops" or "blocked" in item.event_name or "held_for_review" in item.event_name
        ][:40]
        return AnalyticsDashboardResponse(
            dashboard_id="trust",
            title="Trust / Safety Analytics",
            window_grain="rolling",
            summary_metrics=[
                _ops_dashboard_metric("api_error_rate", "API error rate", latest_ops, unit="ratio", max_good=0.05),
                _ops_dashboard_metric("model_failure_rate", "Model failure rate", latest_ops, unit="ratio", max_good=0.05),
                _ops_dashboard_metric("stale_insight_rate", "Stale insight rate", latest_ops, unit="ratio", max_good=0.2),
                _ops_dashboard_metric("moderation_queue_volume", "Moderation queue", latest_ops, unit="count", max_good=100),
                _ops_dashboard_metric("open_trust_incident_count", "Open trust incidents", latest_ops, unit="count", max_good=0),
                _ops_dashboard_metric("critical_trust_incident_count", "Critical incidents", latest_ops, unit="count", max_good=0),
            ],
            module_activity=_module_activity(recent_ops_events),
            recent_events=[_to_event_response(item) for item in recent_trust_events[:25]],
            open_alerts=[_to_alert_response(item) for item in self.repo.list_alerts(status="open", limit=20)],
        )


def _to_kpi_response(item: AnalyticsKpiSnapshot) -> AnalyticsKpiSnapshotResponse:
    return AnalyticsKpiSnapshotResponse(
        snapshot_id=item.snapshot_id,
        kpi_name=item.kpi_name,
        window_grain=item.window_grain,
        window_start=item.window_start,
        window_end=item.window_end,
        value=item.value,
        segment_key=item.segment_key,
        segment_value=item.segment_value,
        meta=json.loads(item.meta_json) if item.meta_json else None,
        created_at=item.created_at,
    )


def _to_ops_metric_response(item: OpsMetricSnapshot) -> OpsMetricSnapshotResponse:
    return OpsMetricSnapshotResponse(
        snapshot_id=item.snapshot_id,
        metric_name=item.metric_name,
        metric_group=item.metric_group,
        surface=item.surface,
        status=item.status,
        value=item.value,
        unit=item.unit,
        captured_at=item.captured_at,
        meta=json.loads(item.meta_json) if item.meta_json else None,
    )


def _to_alert_response(item: OpsAlertEvent) -> OpsAlertEventResponse:
    return OpsAlertEventResponse(
        alert_id=item.alert_id,
        rule_name=item.rule_name,
        severity_tier=item.severity_tier,
        surface=item.surface,
        status=item.status,
        summary=item.summary,
        details=json.loads(item.details_json) if item.details_json else None,
        triggered_at=item.triggered_at,
        resolved_at=item.resolved_at,
    )


def _to_event_response(item: AnalyticsEvent) -> AnalyticsEventResponse:
    return AnalyticsEventResponse(
        event_id=item.event_id,
        event_name=item.event_name,
        event_category=item.event_category,
        timestamp=item.timestamp,
        module=item.module,
        surface=item.surface,
        user_id=item.user_id,
        session_id=item.session_id,
        persona_segment=item.persona_segment,
        route=item.route,
        source_surface=item.source_surface,
        target_surface=item.target_surface,
        properties=json.loads(item.properties_json) if item.properties_json else None,
    )


def _latest_kpi_map(repo: SqliteAnalyticsMonitoringRepository, *, window_grain: str) -> dict[str, AnalyticsKpiSnapshot]:
    items = repo.list_kpi_snapshots(window_grain=window_grain, limit=200)
    latest: dict[str, AnalyticsKpiSnapshot] = {}
    for item in items:
        latest.setdefault(item.kpi_name, item)
    return latest


def _latest_ops_map(repo: SqliteAnalyticsMonitoringRepository) -> dict[str, OpsMetricSnapshot]:
    items = repo.list_ops_metric_snapshots(limit=200)
    latest: dict[str, OpsMetricSnapshot] = {}
    for item in items:
        latest.setdefault(item.metric_name, item)
    return latest


def _dashboard_metric(
    key: str,
    label: str,
    latest_kpis: dict[str, AnalyticsKpiSnapshot],
    *,
    unit: str,
    status_good_threshold: float | None = None,
) -> AnalyticsDashboardMetricResponse:
    item = latest_kpis.get(key)
    value = float(item.value) if item is not None else 0.0
    status = "good" if status_good_threshold is None or value >= status_good_threshold else "degraded"
    return AnalyticsDashboardMetricResponse(key=key, label=label, value=value, unit=unit, status=status)


def _ops_dashboard_metric(
    key: str,
    label: str,
    latest_ops: dict[str, OpsMetricSnapshot],
    *,
    unit: str,
    max_good: float,
) -> AnalyticsDashboardMetricResponse:
    item = latest_ops.get(key)
    value = float(item.value) if item is not None else 0.0
    status = "good" if value <= max_good else "degraded"
    context = item.surface if item is not None else None
    return AnalyticsDashboardMetricResponse(key=key, label=label, value=value, unit=unit, status=status, context=context)


def _module_activity(events: list[AnalyticsEvent]) -> list[AnalyticsDashboardModuleResponse]:
    by_module: dict[str, dict[str, object]] = {}
    for item in events:
        current = by_module.setdefault(
            item.module,
            {"event_count": 0, "sessions": set(), "last_event_at": None},
        )
        current["event_count"] = int(current["event_count"]) + 1
        if item.session_id:
            cast_sessions = current["sessions"]
            assert isinstance(cast_sessions, set)
            cast_sessions.add(item.session_id)
        last_event_at = current["last_event_at"]
        if not last_event_at or item.timestamp > str(last_event_at):
            current["last_event_at"] = item.timestamp
    ordered = sorted(
        by_module.items(),
        key=lambda pair: int(pair[1]["event_count"]),
        reverse=True,
    )
    return [
        AnalyticsDashboardModuleResponse(
            module=module,
            event_count=int(payload["event_count"]),
            unique_sessions=len(payload["sessions"]),
            last_event_at=str(payload["last_event_at"]) if payload["last_event_at"] else None,
        )
        for module, payload in ordered
    ]
