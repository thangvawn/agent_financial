from __future__ import annotations

import json
import sqlite3
from typing import Any

from risk_dashboard.modules.news_intelligence.domain.ports import BriefRepositoryPort
from risk_dashboard.modules.news_intelligence.schemas.agent_tools import (
    EvidenceRow,
    NewsEvidenceBriefArtifact,
)
from risk_dashboard.platform.database import open_app_state_db


class SqliteBriefRepository(BriefRepositoryPort):
    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._db_path:
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            return conn
        return open_app_state_db()

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS news_evidence_briefs (
                    brief_id TEXT PRIMARY KEY,
                    artifact_id TEXT NOT NULL,
                    authoring_run_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    cluster_ids TEXT NOT NULL,
                    evidence_rows_json TEXT NOT NULL,
                    source_coverage REAL NOT NULL,
                    limitations_json TEXT NOT NULL,
                    review_status TEXT NOT NULL,
                    evidence_hash TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_news_briefs_account ON news_evidence_briefs(account_id);"
            )
            conn.commit()

    def save(self, brief: NewsEvidenceBriefArtifact) -> str:
        with self._get_connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO news_evidence_briefs (
                        brief_id, artifact_id, authoring_run_id, account_id, title,
                        objective, cluster_ids, evidence_rows_json, source_coverage,
                        limitations_json, review_status, evidence_hash, version,
                        created_at, expires_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        brief.brief_id,
                        brief.artifact_id,
                        brief.authoring_run_id,
                        brief.account_id,
                        brief.title,
                        brief.objective,
                        json.dumps(list(brief.cluster_ids)),
                        json.dumps([row.model_dump() for row in brief.evidence_rows]),
                        brief.source_coverage,
                        json.dumps(list(brief.limitations)),
                        brief.review_status,
                        brief.evidence_hash,
                        brief.version,
                        brief.created_at,
                        brief.expires_at,
                    ),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                raise ValueError(
                    f"NEWS_BRIEF_ALREADY_EXISTS: Brief or proposal '{brief.brief_id}' has already been saved."
                )
        return brief.brief_id

    def get(self, brief_id: str, account_id: str) -> NewsEvidenceBriefArtifact | None:
        if not account_id:
            return None
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM news_evidence_briefs WHERE brief_id = ? AND account_id = ?",
                (brief_id, account_id),
            ).fetchone()
            if not row:
                return None
            return self._row_to_artifact(row)

    def list_by_account(self, account_id: str) -> list[NewsEvidenceBriefArtifact]:
        if not account_id:
            return []
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM news_evidence_briefs WHERE account_id = ? ORDER BY created_at DESC",
                (account_id,),
            ).fetchall()
            return [self._row_to_artifact(r) for r in rows]

    def _row_to_artifact(self, row: sqlite3.Row | dict[str, Any]) -> NewsEvidenceBriefArtifact:
        raw = dict(row)
        cluster_ids = tuple(json.loads(raw["cluster_ids"]))
        limitations = tuple(json.loads(raw["limitations_json"]))
        raw_evidence_rows = json.loads(raw["evidence_rows_json"])
        evidence_rows = tuple(EvidenceRow.model_validate(r) for r in raw_evidence_rows)

        return NewsEvidenceBriefArtifact(
            schema_version="1.0.0",
            brief_id=raw["brief_id"],
            artifact_id=raw["artifact_id"],
            authoring_run_id=raw["authoring_run_id"],
            account_id=raw["account_id"],
            title=raw["title"],
            objective=raw["objective"],
            cluster_ids=cluster_ids,
            evidence_rows=evidence_rows,
            source_coverage=float(raw["source_coverage"]),
            limitations=limitations,
            review_status=raw["review_status"],
            evidence_hash=raw["evidence_hash"],
            version=int(raw["version"]),
            created_at=raw["created_at"],
            expires_at=raw["expires_at"],
        )
