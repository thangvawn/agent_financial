from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from risk_dashboard.modules.analytics_monitoring.application.services import (
    ListAlerts,
    ListAnalyticsEvents,
    ListKpiSnapshots,
    ListOpsMetrics,
)
from risk_dashboard.modules.analytics_monitoring.infrastructure.repositories.sqlite import (
    SqliteAnalyticsMonitoringRepository,
)
from risk_dashboard.modules.internal_ops.application.policy import PolicyEngine, PurposeGrant
from risk_dashboard.modules.internal_ops.application.redaction import RedactionEngine
from risk_dashboard.modules.internal_ops.domain.contracts import (
    EvidenceBatch,
    EvidenceItem,
    EvidenceRef,
)

KPI_ALLOWLIST = {"kpi_name", "window_grain", "metric_value", "target_value", "status", "as_of"}
METRIC_ALLOWLIST = {"metric_group", "metric_name", "status", "value", "as_of", "details"}
ALERT_ALLOWLIST = {"alert_id", "alert_name", "severity", "status", "triggered_at", "details"}
EVENT_ALLOWLIST = {"event_name", "event_category", "module", "surface", "timestamp", "properties"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AnalyticsAdapter:
    """Direct in-process adapter to Analytics Monitoring services. Zero HTTP loopback."""

    def __init__(
        self,
        list_kpi_service: ListKpiSnapshots | None = None,
        list_events_service: ListAnalyticsEvents | None = None,
        list_metrics_service: ListOpsMetrics | None = None,
        list_alerts_service: ListAlerts | None = None,
    ) -> None:
        repo = SqliteAnalyticsMonitoringRepository()
        self._list_kpis = list_kpi_service or ListKpiSnapshots(repo=repo)
        self._list_events = list_events_service or ListAnalyticsEvents(repo=repo)
        self._list_metrics = list_metrics_service or ListOpsMetrics(repo=repo)
        self._list_alerts = list_alerts_service or ListAlerts(repo=repo)

    def get_kpi_slice(
        self,
        grant: PurposeGrant,
        kpi_name: str | None = None,
        window: str | None = None,
    ) -> EvidenceBatch:
        PolicyEngine.authorize_tool_call(grant, "ops.get_kpi_slice@1.0.0", "analytics_monitoring")
        results = self._list_kpis.execute(kpi_name=kpi_name, window_grain=window)

        items: list[EvidenceItem] = []
        now_iso = _utc_now_iso()
        for snap in results:
            raw_dict = snap.model_dump() if hasattr(snap, "model_dump") else dict(snap)
            clean_fields, reds = RedactionEngine.filter_and_redact_dict(raw_dict, KPI_ALLOWLIST)
            ref = EvidenceRef(
                source_module="analytics_monitoring",
                resource_type="kpi_snapshot",
                resource_id=clean_fields.get("kpi_name", "unknown_kpi"),
                observed_at=clean_fields.get("as_of", now_iso),
            )
            items.append(
                EvidenceItem(
                    ref=ref,
                    classification="aggregate",
                    fields=clean_fields,
                    redactions=tuple(reds),
                )
            )
        return EvidenceBatch(
            items=tuple(items),
            source_module="analytics_monitoring",
            fetched_at=now_iso,
            status="available",
        )

    def get_analytics_events(
        self,
        grant: PurposeGrant,
        event_name: str | None = None,
        limit: int = 100,
    ) -> EvidenceBatch:
        PolicyEngine.authorize_tool_call(grant, "ops.get_analytics_events@1.0.0", "analytics_monitoring")
        capped_limit = min(max(limit, 1), 500)
        results = self._list_events.execute(event_name=event_name, limit=capped_limit)

        items: list[EvidenceItem] = []
        now_iso = _utc_now_iso()
        for evt in results:
            raw_dict = evt.model_dump() if hasattr(evt, "model_dump") else dict(evt)
            clean_fields, reds = RedactionEngine.filter_and_redact_dict(raw_dict, EVENT_ALLOWLIST)
            ref = EvidenceRef(
                source_module="analytics_monitoring",
                resource_type="analytics_event",
                resource_id=clean_fields.get("event_name", "event"),
                observed_at=clean_fields.get("timestamp", now_iso),
            )
            items.append(
                EvidenceItem(
                    ref=ref,
                    classification="metadata",
                    fields=clean_fields,
                    redactions=tuple(reds),
                )
            )
        return EvidenceBatch(
            items=tuple(items),
            source_module="analytics_monitoring",
            fetched_at=now_iso,
            status="available",
        )

    def get_source_health(
        self,
        grant: PurposeGrant,
        metric_group: str = "data_freshness",
    ) -> EvidenceBatch:
        PolicyEngine.authorize_tool_call(grant, "ops.get_source_health@1.0.0", "analytics_monitoring")
        results = self._list_metrics.execute(metric_group=metric_group)

        items: list[EvidenceItem] = []
        now_iso = _utc_now_iso()
        for m in results:
            raw_dict = m.model_dump() if hasattr(m, "model_dump") else dict(m)
            clean_fields, reds = RedactionEngine.filter_and_redact_dict(raw_dict, METRIC_ALLOWLIST)
            ref = EvidenceRef(
                source_module="analytics_monitoring",
                resource_type="ops_metric",
                resource_id=clean_fields.get("metric_name", "metric"),
                observed_at=clean_fields.get("as_of", now_iso),
            )
            items.append(
                EvidenceItem(
                    ref=ref,
                    classification="metadata",
                    fields=clean_fields,
                    redactions=tuple(reds),
                )
            )
        return EvidenceBatch(
            items=tuple(items),
            source_module="analytics_monitoring",
            fetched_at=now_iso,
            status="available",
        )

    def get_alert_context(
        self,
        grant: PurposeGrant,
        status: str | None = None,
    ) -> EvidenceBatch:
        PolicyEngine.authorize_tool_call(grant, "ops.get_alert_context@1.0.0", "analytics_monitoring")
        results = self._list_alerts.execute(status=status)

        items: list[EvidenceItem] = []
        now_iso = _utc_now_iso()
        for a in results:
            raw_dict = a.model_dump() if hasattr(a, "model_dump") else dict(a)
            clean_fields, reds = RedactionEngine.filter_and_redact_dict(raw_dict, ALERT_ALLOWLIST)
            ref = EvidenceRef(
                source_module="analytics_monitoring",
                resource_type="ops_alert",
                resource_id=str(clean_fields.get("alert_id", "alert")),
                observed_at=clean_fields.get("triggered_at", now_iso),
            )
            items.append(
                EvidenceItem(
                    ref=ref,
                    classification="metadata",
                    fields=clean_fields,
                    redactions=tuple(reds),
                )
            )
        return EvidenceBatch(
            items=tuple(items),
            source_module="analytics_monitoring",
            fetched_at=now_iso,
            status="available",
        )

