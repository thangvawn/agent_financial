from __future__ import annotations

import pytest

from risk_dashboard.modules.agentic_core.infrastructure.migrations import ensure_agentic_tables
from risk_dashboard.modules.agentic_core.infrastructure.repositories import (
    AgenticActionRepository,
    AgenticArtifactRepository,
    AgenticMemoryRepository,
    AgenticRunRepository,
)
from risk_dashboard.modules.agentic_core.schemas.artifact import ActionProposal, ActionReceipt, AgentArtifact
from risk_dashboard.modules.agentic_core.schemas.envelope import ResourceRef
from risk_dashboard.modules.agentic_core.schemas.memory import MemoryProposal
from risk_dashboard.modules.agentic_core.schemas.runs import AgentRun
from risk_dashboard.platform.database import open_app_state_db
from risk_dashboard.platform.database.migrate import apply_migrations

NOW = "2026-08-28T12:00:00+00:00"


def test_migration_016_agentic_core_applies(tmp_path) -> None:
    db_path = tmp_path / "migration_test.db"
    with open_app_state_db(db_path) as conn:
        applied = [r[0] for r in conn.execute("SELECT id FROM schema_migrations").fetchall()]
        assert "016_agentic_core" in applied
        # Verify tables and views exist
        entities = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'view') AND name LIKE 'agentic_%'"
            ).fetchall()
        ]
        assert "agentic_runs" in entities
        assert "agentic_artifacts" in entities
        assert "agentic_action_proposals" in entities
        assert "agentic_action_receipts" in entities
        assert "agentic_memory_proposals" in entities
        assert "agentic_core_runs" in entities
        assert "agentic_core_artifacts" in entities
        assert "agentic_core_action_proposals" in entities


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
            correlation_id="corr-1",
            idempotency_key="idem-1",
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

        # Test run idempotency lookup
        assert runs.get_by_idempotency(conn, account_id="account-a", idempotency_key="idem-1") is not None
        assert runs.get_by_idempotency(conn, account_id="account-b", idempotency_key="idem-1") is None

        # Cross-account run overwrite fails
        with pytest.raises(ValueError, match="another account"):
            runs.save(
                conn,
                run_id="run-1",
                account_id="account-b",
                surface="pro_lab",
                status="tampered",
                created_at=NOW,
                updated_at=NOW,
            )


def test_action_and_memory_persistence(tmp_path) -> None:
    db_path = tmp_path / "actions.db"
    actions = AgenticActionRepository()
    memories = AgenticMemoryRepository()

    proposal = ActionProposal(
        proposal_id="prop-1",
        run_id="run-1",
        account_id="account-a",
        operation="export_report",
        target=ResourceRef(kind="report", resource_id="r1", module="pro_lab"),
        payload_preview={"format": "pdf"},
        risk_class="proposal",
        policy_version="1.0.0",
        created_at=NOW,
        expires_at="2026-08-28T13:00:00+00:00",
    )
    receipt = ActionReceipt(
        receipt_id="rcpt-1",
        proposal_id="prop-1",
        account_id="account-a",
        status="executed",
        executed_at=NOW,
    )
    memory = MemoryProposal(
        proposal_id="mem-1",
        run_id="run-1",
        account_id="account-a",
        memory_type="preference",
        content="Prefer detailed explanations",
        provenance="user_stated",
        created_at=NOW,
    )

    with open_app_state_db(db_path) as conn:
        ensure_agentic_tables(conn)
        actions.save_proposal(conn, proposal)
        actions.save_receipt(conn, receipt)
        memories.save_proposal(conn, memory)

        # Scoped retrieval
        assert actions.get_proposal(conn, proposal_id="prop-1", account_id="account-a") is not None
        assert actions.get_proposal(conn, proposal_id="prop-1", account_id="account-b") is None
        assert actions.get_receipt(conn, proposal_id="prop-1", account_id="account-a") is not None
        assert actions.get_receipt(conn, proposal_id="prop-1", account_id="account-b") is None

        assert memories.get_proposal(conn, proposal_id="mem-1", account_id="account-a") is not None
        assert memories.get_proposal(conn, proposal_id="mem-1", account_id="account-b") is None
