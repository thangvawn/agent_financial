from __future__ import annotations

import pytest

from risk_dashboard.modules.agentic_core.infrastructure.migrations import ensure_agentic_tables
from risk_dashboard.modules.agentic_core.infrastructure.repositories import (
    AgenticArtifactRepository,
    AgenticRunRepository,
)
from risk_dashboard.modules.agentic_core.schemas.artifact import AgentArtifact
from risk_dashboard.platform.database import open_app_state_db


NOW = "2026-08-28T12:00:00+00:00"


def test_repositories_scope_rows_to_owner(tmp_path) -> None:
    db_path = tmp_path / "agentic.db"
    runs = AgenticRunRepository()
    artifacts = AgenticArtifactRepository()
    artifact = AgentArtifact(
        artifact_id="artifact-1",
        artifact_type="analysis",
        domain="finance",
        account_id="account-a",
        authoring_run_id="run-1",
        created_at=NOW,
    )

    with open_app_state_db(db_path) as conn:
        ensure_agentic_tables(conn)
        runs.save(
            conn,
            run_id="run-1",
            account_id="account-a",
            surface="pro_lab",
            status="created",
            created_at=NOW,
            updated_at=NOW,
        )
        artifacts.save(conn, artifact)
        assert runs.get(conn, run_id="run-1", account_id="account-a") is not None
        assert runs.get(conn, run_id="run-1", account_id="account-b") is None
        assert artifacts.get(conn, artifact_id="artifact-1", account_id="account-a") == artifact
        assert artifacts.get(conn, artifact_id="artifact-1", account_id="account-b") is None
        with pytest.raises(ValueError, match="another account"):
            artifacts.save(conn, artifact.model_copy(update={"account_id": "account-b"}))
