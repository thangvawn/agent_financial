from __future__ import annotations

import json
import uuid

from risk_dashboard.modules.trust_safety.domain.entities import TrustAuditLog, TrustIncident, TrustSurfaceControl
from risk_dashboard.platform.database import open_app_state_db, reset_app_state_tables


def new_trust_audit_id() -> str:
    return f"trust_{uuid.uuid4().hex[:12]}"


def new_trust_incident_id() -> str:
    return f"incident_{uuid.uuid4().hex[:12]}"


class SqliteTrustSafetyRepository:
    def save_audit_log(self, log: TrustAuditLog) -> TrustAuditLog:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO trust_safety_audit_logs (
                  audit_id, actor_id, surface, topic, channel, risk_classes_json, severity,
                  route_decision, input_summary, output_summary, guardrails_json,
                  disclaimer_injected, freshness_status, confidence_label, escalation_action, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log.audit_id,
                    log.actor_id,
                    log.surface,
                    log.topic,
                    log.channel,
                    json.dumps(list(log.risk_classes), ensure_ascii=False),
                    log.severity,
                    log.route_decision,
                    log.input_summary,
                    log.output_summary,
                    json.dumps(list(log.guardrails), ensure_ascii=False),
                    1 if log.disclaimer_injected else 0,
                    log.freshness_status,
                    log.confidence_label,
                    log.escalation_action,
                    log.created_at,
                ),
            )
            conn.commit()
        return log

    def list_audit_logs(
        self,
        *,
        surface: str | None = None,
        risk_class: str | None = None,
        severity: str | None = None,
        search: str | None = None,
        limit: int = 100,
    ) -> list[TrustAuditLog]:
        query = "SELECT * FROM trust_safety_audit_logs"
        clauses: list[str] = []
        params: list[object] = []
        if surface:
            clauses.append("surface = ?")
            params.append(surface)
        if severity:
            clauses.append("severity = ?")
            params.append(severity)
        if search:
            clauses.append(
                "(COALESCE(topic, '') LIKE ? OR COALESCE(input_summary, '') LIKE ? OR COALESCE(output_summary, '') LIKE ? OR COALESCE(route_decision, '') LIKE ? OR COALESCE(channel, '') LIKE ?)"
            )
            pattern = f"%{search.strip()}%"
            params.extend([pattern, pattern, pattern, pattern, pattern])
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with open_app_state_db() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        items = [
            TrustAuditLog(
                audit_id=row["audit_id"],
                actor_id=row["actor_id"],
                surface=row["surface"],
                topic=row["topic"],
                channel=row["channel"],
                risk_classes=tuple(json.loads(row["risk_classes_json"] or "[]")),
                severity=row["severity"],
                route_decision=row["route_decision"],
                input_summary=row["input_summary"],
                output_summary=row["output_summary"],
                guardrails=tuple(json.loads(row["guardrails_json"] or "[]")),
                disclaimer_injected=bool(row["disclaimer_injected"]),
                freshness_status=row["freshness_status"],
                confidence_label=row["confidence_label"],
                escalation_action=row["escalation_action"],
                created_at=row["created_at"],
            )
            for row in rows
        ]
        if risk_class:
            return [item for item in items if risk_class in item.risk_classes]
        return items

    def overview(self) -> dict[str, object]:
        controls = self.list_active_surface_controls()
        with open_app_state_db() as conn:
            total = conn.execute("SELECT COUNT(*) AS count FROM trust_safety_audit_logs").fetchone()["count"]
            critical = conn.execute(
                "SELECT COUNT(*) AS count FROM trust_safety_audit_logs WHERE severity = 'critical'"
            ).fetchone()["count"]
            blocked = conn.execute(
                "SELECT COUNT(*) AS count FROM trust_safety_audit_logs WHERE route_decision IN ('blocked_for_safety', 'blocked', 'blocked_by_trust_safety')"
            ).fetchone()["count"]
            missing_disclaimer = conn.execute(
                "SELECT COUNT(*) AS count FROM trust_safety_audit_logs WHERE disclaimer_injected = 1"
            ).fetchone()["count"]
        return {
            "total_events": int(total),
            "critical_events": int(critical),
            "blocked_events": int(blocked),
            "default_disclaimer_injections": int(missing_disclaimer),
            "frozen_surfaces": sum(1 for item in controls if item.state == "freeze"),
            "degraded_surfaces": sum(1 for item in controls if item.state == "degrade"),
        }

    def save_incident(self, incident: TrustIncident) -> TrustIncident:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO trust_safety_incidents (
                  incident_id, source_audit_id, surface, topic, severity, status, summary,
                  owner_id, notes, created_by, created_at, updated_at, resolved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(incident_id) DO UPDATE SET
                  source_audit_id = excluded.source_audit_id,
                  surface = excluded.surface,
                  topic = excluded.topic,
                  severity = excluded.severity,
                  status = excluded.status,
                  summary = excluded.summary,
                  owner_id = excluded.owner_id,
                  notes = excluded.notes,
                  updated_at = excluded.updated_at,
                  resolved_at = excluded.resolved_at
                """,
                (
                    incident.incident_id,
                    incident.source_audit_id,
                    incident.surface,
                    incident.topic,
                    incident.severity,
                    incident.status,
                    incident.summary,
                    incident.owner_id,
                    incident.notes,
                    incident.created_by,
                    incident.created_at,
                    incident.updated_at,
                    incident.resolved_at,
                ),
            )
            conn.commit()
        return incident

    def list_incidents(
        self,
        *,
        status: str | None = None,
        surface: str | None = None,
        severity: str | None = None,
        search: str | None = None,
        limit: int = 100,
    ) -> list[TrustIncident]:
        query = "SELECT * FROM trust_safety_incidents"
        clauses: list[str] = []
        params: list[object] = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if surface:
            clauses.append("surface = ?")
            params.append(surface)
        if severity:
            clauses.append("severity = ?")
            params.append(severity)
        if search:
            clauses.append("(COALESCE(topic, '') LIKE ? OR COALESCE(summary, '') LIKE ? OR COALESCE(notes, '') LIKE ?)")
            pattern = f"%{search.strip()}%"
            params.extend([pattern, pattern, pattern])
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY updated_at DESC, created_at DESC LIMIT ?"
        params.append(limit)
        with open_app_state_db() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [
            TrustIncident(
                incident_id=row["incident_id"],
                source_audit_id=row["source_audit_id"],
                surface=row["surface"],
                topic=row["topic"],
                severity=row["severity"],
                status=row["status"],
                summary=row["summary"],
                owner_id=row["owner_id"],
                notes=row["notes"],
                created_by=row["created_by"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                resolved_at=row["resolved_at"],
            )
            for row in rows
        ]

    def get_incident(self, *, incident_id: str) -> TrustIncident | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                "SELECT * FROM trust_safety_incidents WHERE incident_id = ?",
                (incident_id,),
            ).fetchone()
        if row is None:
            return None
        return TrustIncident(
            incident_id=row["incident_id"],
            source_audit_id=row["source_audit_id"],
            surface=row["surface"],
            topic=row["topic"],
            severity=row["severity"],
            status=row["status"],
            summary=row["summary"],
            owner_id=row["owner_id"],
            notes=row["notes"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            resolved_at=row["resolved_at"],
        )

    def list_active_surface_controls(self) -> list[TrustSurfaceControl]:
        incidents = self.list_incidents(limit=500)
        controls: dict[str, TrustSurfaceControl] = {}
        for incident in incidents:
            if incident.status not in {"open", "investigating", "mitigated"}:
                continue
            if incident.severity == "critical" and incident.status in {"open", "investigating"}:
                candidate = TrustSurfaceControl(
                    surface=incident.surface,
                    state="freeze",
                    severity=incident.severity,
                    incident_id=incident.incident_id,
                    reason=incident.summary,
                )
            elif incident.severity in {"high", "critical"}:
                candidate = TrustSurfaceControl(
                    surface=incident.surface,
                    state="degrade",
                    severity=incident.severity,
                    incident_id=incident.incident_id,
                    reason=incident.summary,
                )
            else:
                continue
            current = controls.get(incident.surface)
            if current is None or current.state != "freeze":
                controls[incident.surface] = candidate
        return list(controls.values())

    def get_surface_control(self, *, surface: str) -> TrustSurfaceControl | None:
        for item in self.list_active_surface_controls():
            if item.surface == surface:
                return item
        return None


def reset_trust_safety_state() -> None:
    reset_app_state_tables()
