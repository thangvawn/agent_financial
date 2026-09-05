from __future__ import annotations

import json
import sqlite3
from typing import Any, Callable
import uuid

from risk_dashboard.modules.internal_ops.application.policy import utc_now
from risk_dashboard.modules.internal_ops.domain.contracts import (
    EvidenceItem,
    InvestigationRequest,
    OpsInvestigationReport,
)
from risk_dashboard.modules.internal_ops.infrastructure.schema import init_ops_tables
from risk_dashboard.platform.database import open_app_state_db

_DEFAULT_TABLES_INITIALIZED = False


class SqliteInternalOpsRepository:
    def __init__(self, conn_factory: Callable[[], Any] | None = None) -> None:
        global _DEFAULT_TABLES_INITIALIZED
        self._conn_factory = conn_factory or open_app_state_db
        if conn_factory is not None or not _DEFAULT_TABLES_INITIALIZED:
            with self._conn_factory() as conn:
                init_ops_tables(conn)
            if conn_factory is None:
                _DEFAULT_TABLES_INITIALIZED = True


    def save_investigation(
        self,
        investigation_id: str,
        account_id: str,
        request: InvestigationRequest,
        report: OpsInvestigationReport,
        evidence_items: list[EvidenceItem],
    ) -> None:
        now_iso = utc_now().isoformat()
        with self._conn_factory() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO internal_ops_investigations (
                    investigation_id, account_id, investigation_type, purpose, status, request_json, report_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    investigation_id,
                    account_id,
                    request.investigation_type,
                    request.purpose,
                    report.status,
                    json.dumps(request.model_dump()),
                    json.dumps(report.model_dump()),
                    now_iso,
                    now_iso,
                ),
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO internal_ops_reports (
                    report_id, investigation_id, account_id, status, severity, payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report.report_id,
                    investigation_id,
                    account_id,
                    report.status,
                    report.severity,
                    json.dumps(report.model_dump()),
                    now_iso,
                ),
            )
            for item in evidence_items:
                ev_id = f"ev-{uuid.uuid4().hex[:12]}"
                conn.execute(
                    """
                    INSERT INTO internal_ops_evidence (
                        evidence_id, investigation_id, source_module, resource_type, resource_id, item_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ev_id,
                        investigation_id,
                        item.ref.source_module,
                        item.ref.resource_type,
                        item.ref.resource_id,
                        json.dumps(item.model_dump()),
                        now_iso,
                    ),
                )
            conn.commit()

    def get_investigation(self, investigation_id: str) -> tuple[str, OpsInvestigationReport] | None:
        with self._conn_factory() as conn:
            row = conn.execute(
                "SELECT account_id, report_json FROM internal_ops_investigations WHERE investigation_id = ?",
                (investigation_id,),
            ).fetchone()
            if not row or not row[1]:
                return None
            account_id, report_json = row[0], row[1]
            report = OpsInvestigationReport.model_validate(json.loads(report_json))
            return account_id, report

    def get_evidence(
        self,
        investigation_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[EvidenceItem], int]:
        capped_limit = min(max(limit, 1), 500)
        with self._conn_factory() as conn:
            total_row = conn.execute(
                "SELECT COUNT(*) FROM internal_ops_evidence WHERE investigation_id = ?",
                (investigation_id,),
            ).fetchone()
            total = total_row[0] if total_row else 0

            rows = conn.execute(
                """
                SELECT item_json FROM internal_ops_evidence
                WHERE investigation_id = ?
                ORDER BY created_at ASC
                LIMIT ? OFFSET ?
                """,
                (investigation_id, capped_limit, offset),
            ).fetchall()

            items = [EvidenceItem.model_validate(json.loads(r[0])) for r in rows]
            return items, total

    def record_audit(
        self,
        account_id: str,
        decision: str,
        purpose: str,
        investigation_id: str | None = None,
        tool_id: str | None = None,
        scope_snapshot: str = "",
    ) -> str:
        audit_id = f"aud-{uuid.uuid4().hex[:12]}"
        now_iso = utc_now().isoformat()
        with self._conn_factory() as conn:
            conn.execute(
                """
                INSERT INTO internal_ops_access_audit (
                    audit_id, investigation_id, account_id, scope_snapshot, purpose, tool_id, decision, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id,
                    investigation_id,
                    account_id,
                    scope_snapshot,
                    purpose,
                    tool_id,
                    decision,
                    now_iso,
                ),
            )
            conn.commit()
        return audit_id
