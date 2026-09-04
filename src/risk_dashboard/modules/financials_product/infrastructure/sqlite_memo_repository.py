from __future__ import annotations

import json
from datetime import datetime, timezone
import sqlite3
from typing import Any, Sequence

from risk_dashboard.modules.financials_product.domain.ports import MemoRepositoryPort
from risk_dashboard.modules.financials_product.schemas.agent_tools import (
    CalculateRatioOutput,
    EvidenceRow,
    ProvenanceRef,
)
from risk_dashboard.modules.financials_product.schemas.evidence import BCTCEvidenceMemo
from risk_dashboard.platform.database import open_app_state_db


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SqliteMemoRepository(MemoRepositoryPort):
    """SQLite implementation of BCTCEvidenceMemo repository."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        if self._db_path:
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            return conn
        return open_app_state_db()

    def save_memo(self, memo: BCTCEvidenceMemo, account_id: str) -> None:
        now = _now_iso()
        report_refs_json = json.dumps([r.model_dump(mode="json") for r in memo.report_refs])
        evidence_rows_json = json.dumps([r.model_dump(mode="json") for r in memo.evidence_rows])
        calculations_json = json.dumps([c.model_dump(mode="json") for c in memo.calculations])
        interpretations_json = json.dumps(list(memo.interpretations))
        unresolved_json = json.dumps(list(memo.unresolved_questions))
        limitations_json = json.dumps(list(memo.limitations))

        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO bctc_evidence_memos (
                    memo_id, account_id, subject, report_refs_json, scope,
                    evidence_rows_json, calculations_json, interpretations_json,
                    unresolved_questions_json, limitations_json, reviewer_status,
                    is_stale, expires_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(memo_id) DO UPDATE SET
                    subject = excluded.subject,
                    report_refs_json = excluded.report_refs_json,
                    scope = excluded.scope,
                    evidence_rows_json = excluded.evidence_rows_json,
                    calculations_json = excluded.calculations_json,
                    interpretations_json = excluded.interpretations_json,
                    unresolved_questions_json = excluded.unresolved_questions_json,
                    limitations_json = excluded.limitations_json,
                    reviewer_status = excluded.reviewer_status,
                    is_stale = excluded.is_stale,
                    expires_at = excluded.expires_at,
                    updated_at = excluded.updated_at
                """,
                (
                    memo.memo_id,
                    account_id,
                    memo.subject,
                    report_refs_json,
                    memo.scope,
                    evidence_rows_json,
                    calculations_json,
                    interpretations_json,
                    unresolved_json,
                    limitations_json,
                    memo.reviewer_status,
                    1 if memo.is_stale else 0,
                    memo.expires_at,
                    memo.created_at or now,
                    now,
                ),
            )

    def get_memo(self, memo_id: str, account_id: str) -> BCTCEvidenceMemo | None:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM bctc_evidence_memos WHERE memo_id = ? AND account_id = ?",
                (memo_id, account_id),
            ).fetchone()
            if not row:
                return None
            return self._row_to_memo(row)

    def list_memos_by_account(self, account_id: str) -> Sequence[BCTCEvidenceMemo]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM bctc_evidence_memos WHERE account_id = ? ORDER BY created_at DESC",
                (account_id,),
            ).fetchall()
            return [self._row_to_memo(r) for r in rows]

    def mark_stale(self, memo_id: str) -> None:
        now = _now_iso()
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE bctc_evidence_memos SET is_stale = 1, updated_at = ? WHERE memo_id = ?",
                (now, memo_id),
            )

    def delete_memo(self, memo_id: str, account_id: str) -> bool:
        with self._get_conn() as conn:
            cursor = conn.execute(
                "DELETE FROM bctc_evidence_memos WHERE memo_id = ? AND account_id = ?",
                (memo_id, account_id),
            )
            return cursor.rowcount > 0

    def _row_to_memo(self, row: Any) -> BCTCEvidenceMemo:
        report_refs = tuple(ProvenanceRef.model_validate(r) for r in json.loads(row["report_refs_json"]))
        evidence_rows = tuple(EvidenceRow.model_validate(r) for r in json.loads(row["evidence_rows_json"]))
        calculations = tuple(CalculateRatioOutput.model_validate(c) for c in json.loads(row["calculations_json"]))
        interpretations = tuple(json.loads(row["interpretations_json"]))
        unresolved = tuple(json.loads(row["unresolved_questions_json"]))
        limitations = tuple(json.loads(row["limitations_json"]))

        return BCTCEvidenceMemo(
            schema_version="1.0.0",
            memo_id=row["memo_id"],
            subject=row["subject"],
            report_refs=report_refs,
            scope=row["scope"],
            evidence_rows=evidence_rows,
            calculations=calculations,
            interpretations=interpretations,
            unresolved_questions=unresolved,
            limitations=limitations,
            reviewer_status=row["reviewer_status"],
            is_stale=bool(row["is_stale"]),
            expires_at=row["expires_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

