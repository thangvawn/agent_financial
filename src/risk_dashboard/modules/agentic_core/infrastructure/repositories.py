from __future__ import annotations

import json

from risk_dashboard.modules.agentic_core.infrastructure.migrations import ensure_agentic_tables
from risk_dashboard.modules.agentic_core.schemas.artifact import AgentArtifact


class AgenticRunRepository:
    def save(
        self,
        conn,
        *,
        run_id: str,
        account_id: str,
        surface: str,
        status: str,
        created_at: str,
        updated_at: str,
    ) -> None:
        ensure_agentic_tables(conn)
        conn.execute(
            """
            INSERT INTO agentic_runs (run_id, account_id, surface, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET status = excluded.status, updated_at = excluded.updated_at
            """,
            (run_id, account_id, surface, status, created_at, updated_at),
        )

    def get(self, conn, *, run_id: str, account_id: str):
        ensure_agentic_tables(conn)
        return conn.execute(
            "SELECT * FROM agentic_runs WHERE run_id = ? AND account_id = ?",
            (run_id, account_id),
        ).fetchone()


class AgenticArtifactRepository:
    def save(self, conn, artifact: AgentArtifact) -> None:
        ensure_agentic_tables(conn)
        owner = conn.execute(
            "SELECT account_id FROM agentic_artifacts WHERE artifact_id = ?",
            (artifact.artifact_id,),
        ).fetchone()
        if owner is not None and owner["account_id"] != artifact.account_id:
            raise ValueError("Artifact belongs to another account.")
        conn.execute(
            """
            INSERT INTO agentic_artifacts (
              artifact_id, account_id, authoring_run_id, artifact_type, domain,
              review_status, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(artifact_id) DO UPDATE SET
              review_status = excluded.review_status, payload_json = excluded.payload_json
            """,
            (
                artifact.artifact_id,
                artifact.account_id,
                artifact.authoring_run_id,
                artifact.artifact_type,
                artifact.domain,
                artifact.review_status,
                json.dumps(artifact.model_dump(mode="json")),
                artifact.created_at,
            ),
        )

    def get(self, conn, *, artifact_id: str, account_id: str) -> AgentArtifact | None:
        ensure_agentic_tables(conn)
        row = conn.execute(
            """
            SELECT payload_json FROM agentic_artifacts
            WHERE artifact_id = ? AND account_id = ?
            """,
            (artifact_id, account_id),
        ).fetchone()
        return None if row is None else AgentArtifact.model_validate_json(row["payload_json"])
