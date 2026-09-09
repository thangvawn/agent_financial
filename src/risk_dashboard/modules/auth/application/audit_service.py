from __future__ import annotations

from datetime import datetime, timezone
import sqlite3
from typing import Any
import uuid
from pydantic import BaseModel

from risk_dashboard.platform.database import open_app_state_db


class AuditEvent(BaseModel):
    schema_version: str = "1.0.0"
    event_id: str
    event_type: str
    actor_id: str
    target_account_id: str | None = None
    reason: str | None = None
    details: dict[str, Any] = {}
    created_at: str


class AuditLogService:
    """Append-only audit service for security, break-glass and privacy events."""

    def __init__(self) -> None:
        self._ensure_table()

    def _ensure_table(self) -> None:
        with open_app_state_db() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_security_logs (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    target_account_id TEXT,
                    reason TEXT,
                    details_json TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def log_event(
        self,
        *,
        event_type: str,
        actor_id: str,
        target_account_id: str | None = None,
        reason: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event_id = f"audit_{uuid.uuid4().hex}"
        now_iso = datetime.now(timezone.utc).isoformat()
        import json

        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            actor_id=actor_id,
            target_account_id=target_account_id,
            reason=reason,
            details=details or {},
            created_at=now_iso,
        )
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO audit_security_logs (
                    event_id, event_type, actor_id, target_account_id, reason, details_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.event_type,
                    event.actor_id,
                    event.target_account_id,
                    event.reason,
                    json.dumps(event.details),
                    event.created_at,
                ),
            )
            conn.commit()
        return event

    def query_events(
        self,
        *,
        event_type: str | None = None,
        target_account_id: str | None = None,
    ) -> list[AuditEvent]:
        import json

        with open_app_state_db() as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM audit_security_logs WHERE 1=1"
            params: list[Any] = []
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)
            if target_account_id:
                query += " AND target_account_id = ?"
                params.append(target_account_id)
            query += " ORDER BY created_at DESC"
            rows = conn.execute(query, params).fetchall()

        results = []
        for r in rows:
            results.append(
                AuditEvent(
                    event_id=r["event_id"],
                    event_type=r["event_type"],
                    actor_id=r["actor_id"],
                    target_account_id=r["target_account_id"],
                    reason=r["reason"],
                    details=json.loads(r["details_json"] or "{}"),
                    created_at=r["created_at"],
                )
            )
        return results

