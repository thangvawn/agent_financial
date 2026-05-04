from __future__ import annotations

import json
import uuid
from dataclasses import replace

from risk_dashboard.modules.analytics_monitoring.domain.events import (
    AnalyticsEvent,
    AnalyticsKpiSnapshot,
    OpsAlertEvent,
    OpsMetricSnapshot,
    utc_now_iso,
)
from risk_dashboard.platform.database import open_app_state_db, reset_app_state_tables


def new_analytics_event_id() -> str:
    return f"evt_{uuid.uuid4().hex[:16]}"


def new_analytics_snapshot_id() -> str:
    return f"snap_{uuid.uuid4().hex[:16]}"


def new_ops_alert_id() -> str:
    return f"alert_{uuid.uuid4().hex[:16]}"


class SqliteAnalyticsMonitoringRepository:
    def save_events(self, events: list[AnalyticsEvent]) -> list[AnalyticsEvent]:
        if not events:
            return []
        with open_app_state_db() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO analytics_events (
                  event_id, event_name, event_category, schema_version, timestamp, module, surface,
                  user_id, session_id, persona_segment, route, locale, device_type, source_surface,
                  target_surface, properties_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        item.event_id,
                        item.event_name,
                        item.event_category,
                        item.schema_version,
                        item.timestamp,
                        item.module,
                        item.surface,
                        item.user_id,
                        item.session_id,
                        item.persona_segment,
                        item.route,
                        item.locale,
                        item.device_type,
                        item.source_surface,
                        item.target_surface,
                        item.properties_json,
                    )
                    for item in events
                ],
            )
            conn.commit()
        return events

    def list_events(
        self,
        *,
        window_start: str | None = None,
        window_end: str | None = None,
        event_category: str | None = None,
        module: str | None = None,
        surface: str | None = None,
        event_name: str | None = None,
        search: str | None = None,
        limit: int | None = None,
    ) -> list[AnalyticsEvent]:
        query = "SELECT * FROM analytics_events"
        clauses: list[str] = []
        params: list[object] = []
        if window_start:
            clauses.append("timestamp >= ?")
            params.append(window_start)
        if window_end:
            clauses.append("timestamp <= ?")
            params.append(window_end)
        if event_category:
            clauses.append("event_category = ?")
            params.append(event_category)
        if module:
            clauses.append("module = ?")
            params.append(module)
        if surface:
            clauses.append("surface = ?")
            params.append(surface)
        if event_name:
            clauses.append("event_name = ?")
            params.append(event_name)
        if search:
            clauses.append("(event_name LIKE ? OR module LIKE ? OR surface LIKE ? OR properties_json LIKE ?)")
            pattern = f"%{search}%"
            params.extend([pattern, pattern, pattern, pattern])
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY timestamp DESC"
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        with open_app_state_db() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [
            AnalyticsEvent(
                event_id=row["event_id"],
                event_name=row["event_name"],
                event_category=row["event_category"],
                schema_version=row["schema_version"],
                timestamp=row["timestamp"],
                module=row["module"],
                surface=row["surface"],
                user_id=row["user_id"],
                session_id=row["session_id"],
                persona_segment=row["persona_segment"],
                route=row["route"],
                locale=row["locale"],
                device_type=row["device_type"],
                source_surface=row["source_surface"],
                target_surface=row["target_surface"],
                properties_json=row["properties_json"],
            )
            for row in rows
        ]

    def save_kpi_snapshots(self, snapshots: list[AnalyticsKpiSnapshot]) -> list[AnalyticsKpiSnapshot]:
        if not snapshots:
            return []
        with open_app_state_db() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO analytics_kpi_snapshots (
                  snapshot_id, kpi_name, window_grain, window_start, window_end, value,
                  segment_key, segment_value, meta_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        item.snapshot_id,
                        item.kpi_name,
                        item.window_grain,
                        item.window_start,
                        item.window_end,
                        item.value,
                        item.segment_key,
                        item.segment_value,
                        item.meta_json,
                        item.created_at,
                    )
                    for item in snapshots
                ],
            )
            conn.commit()
        return snapshots

    def list_kpi_snapshots(
        self,
        *,
        kpi_name: str | None = None,
        window_grain: str | None = None,
        limit: int = 200,
    ) -> list[AnalyticsKpiSnapshot]:
        query = "SELECT * FROM analytics_kpi_snapshots"
        clauses: list[str] = []
        params: list[object] = []
        if kpi_name:
            clauses.append("kpi_name = ?")
            params.append(kpi_name)
        if window_grain:
            clauses.append("window_grain = ?")
            params.append(window_grain)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY window_end DESC, created_at DESC LIMIT ?"
        params.append(limit)
        with open_app_state_db() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [
            AnalyticsKpiSnapshot(
                snapshot_id=row["snapshot_id"],
                kpi_name=row["kpi_name"],
                window_grain=row["window_grain"],
                window_start=row["window_start"],
                window_end=row["window_end"],
                value=float(row["value"]),
                segment_key=row["segment_key"],
                segment_value=row["segment_value"],
                meta_json=row["meta_json"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def save_ops_metric_snapshots(self, snapshots: list[OpsMetricSnapshot]) -> list[OpsMetricSnapshot]:
        if not snapshots:
            return []
        with open_app_state_db() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO ops_metric_snapshots (
                  snapshot_id, metric_name, metric_group, surface, status, value, unit, captured_at, meta_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        item.snapshot_id,
                        item.metric_name,
                        item.metric_group,
                        item.surface,
                        item.status,
                        item.value,
                        item.unit,
                        item.captured_at,
                        item.meta_json,
                    )
                    for item in snapshots
                ],
            )
            conn.commit()
        return snapshots

    def list_ops_metric_snapshots(
        self,
        *,
        metric_group: str | None = None,
        metric_name: str | None = None,
        limit: int = 200,
    ) -> list[OpsMetricSnapshot]:
        query = "SELECT * FROM ops_metric_snapshots"
        clauses: list[str] = []
        params: list[object] = []
        if metric_group:
            clauses.append("metric_group = ?")
            params.append(metric_group)
        if metric_name:
            clauses.append("metric_name = ?")
            params.append(metric_name)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY captured_at DESC LIMIT ?"
        params.append(limit)
        with open_app_state_db() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [
            OpsMetricSnapshot(
                snapshot_id=row["snapshot_id"],
                metric_name=row["metric_name"],
                metric_group=row["metric_group"],
                surface=row["surface"],
                status=row["status"],
                value=float(row["value"]),
                unit=row["unit"],
                captured_at=row["captured_at"],
                meta_json=row["meta_json"],
            )
            for row in rows
        ]

    def get_latest_ops_metric(self, *, metric_name: str) -> OpsMetricSnapshot | None:
        items = self.list_ops_metric_snapshots(metric_name=metric_name, limit=1)
        return items[0] if items else None

    def save_alert(self, alert: OpsAlertEvent) -> OpsAlertEvent:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO ops_alert_events (
                  alert_id, rule_name, severity_tier, surface, status, summary, details_json, triggered_at, resolved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alert.alert_id,
                    alert.rule_name,
                    alert.severity_tier,
                    alert.surface,
                    alert.status,
                    alert.summary,
                    alert.details_json,
                    alert.triggered_at,
                    alert.resolved_at,
                ),
            )
            conn.commit()
        return alert

    def list_alerts(self, *, status: str | None = None, limit: int = 200) -> list[OpsAlertEvent]:
        query = "SELECT * FROM ops_alert_events"
        params: list[object] = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY triggered_at DESC LIMIT ?"
        params.append(limit)
        with open_app_state_db() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [
            OpsAlertEvent(
                alert_id=row["alert_id"],
                rule_name=row["rule_name"],
                severity_tier=row["severity_tier"],
                surface=row["surface"],
                status=row["status"],
                summary=row["summary"],
                details_json=row["details_json"],
                triggered_at=row["triggered_at"],
                resolved_at=row["resolved_at"],
            )
            for row in rows
        ]

    def get_open_alert(self, *, rule_name: str, surface: str | None) -> OpsAlertEvent | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT * FROM ops_alert_events
                WHERE rule_name = ? AND COALESCE(surface, '') = COALESCE(?, '') AND status = 'open'
                ORDER BY triggered_at DESC LIMIT 1
                """,
                (rule_name, surface),
            ).fetchone()
        if row is None:
            return None
        return OpsAlertEvent(
            alert_id=row["alert_id"],
            rule_name=row["rule_name"],
            severity_tier=row["severity_tier"],
            surface=row["surface"],
            status=row["status"],
            summary=row["summary"],
            details_json=row["details_json"],
            triggered_at=row["triggered_at"],
            resolved_at=row["resolved_at"],
        )

    def resolve_open_alert(self, *, rule_name: str, surface: str | None) -> OpsAlertEvent | None:
        current = self.get_open_alert(rule_name=rule_name, surface=surface)
        if current is None:
            return None
        resolved = replace(current, status="resolved", resolved_at=utc_now_iso())
        return self.save_alert(resolved)

    def count_held_for_review(self) -> int:
        with open_app_state_db() as conn:
            posts = conn.execute(
                "SELECT COUNT(*) AS count FROM community_posts WHERE moderation_status = 'held_for_review'"
            ).fetchone()["count"]
            comments = conn.execute(
                "SELECT COUNT(*) AS count FROM community_comments WHERE moderation_status = 'held_for_review'"
            ).fetchone()["count"]
        return int(posts) + int(comments)

    def count_open_trust_incidents(self, *, severity: str | None = None) -> int:
        query = "SELECT COUNT(*) AS count FROM trust_safety_incidents WHERE status IN ('open', 'investigating', 'mitigated')"
        params: list[object] = []
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        with open_app_state_db() as conn:
            count = conn.execute(query, tuple(params)).fetchone()["count"]
        return int(count)

    def overview(self) -> dict[str, int]:
        with open_app_state_db() as conn:
            total_events = conn.execute("SELECT COUNT(*) AS count FROM analytics_events").fetchone()["count"]
            total_kpis = conn.execute("SELECT COUNT(*) AS count FROM analytics_kpi_snapshots").fetchone()["count"]
            total_ops = conn.execute("SELECT COUNT(*) AS count FROM ops_metric_snapshots").fetchone()["count"]
            open_alerts = conn.execute(
                "SELECT COUNT(*) AS count FROM ops_alert_events WHERE status = 'open'"
            ).fetchone()["count"]
        return {
            "total_events": int(total_events),
            "total_kpi_snapshots": int(total_kpis),
            "total_ops_snapshots": int(total_ops),
            "open_alerts": int(open_alerts),
        }


def reset_analytics_monitoring_state() -> None:
    reset_app_state_tables()
