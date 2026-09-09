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


def test_agentic_memory_repository_ownership_scoping(tmp_path) -> None:
    db_path = tmp_path / "memory_scope.db"
    memories = AgenticMemoryRepository()

    prop_a = MemoryProposal(
        proposal_id="mem-scope-1",
        run_id="run-1",
        account_id="account-alpha",
        memory_type="preference",
        content="Prefer technical analysis",
        provenance="user_stated",
        created_at=NOW,
    )

    with open_app_state_db(db_path) as conn:
        ensure_agentic_tables(conn)
        memories.save_proposal(conn, prop_a)

        # Scoped retrieval by account
        assert memories.get_proposal(conn, proposal_id="mem-scope-1", account_id="account-alpha") is not None
        assert memories.get_proposal(conn, proposal_id="mem-scope-1", account_id="account-beta") is None

        # Cross-account overwrite must fail
        with pytest.raises(ValueError, match="another account"):
            memories.save_proposal(conn, prop_a.model_copy(update={"account_id": "account-beta"}))

        # list_proposals isolation
        props_alpha = memories.list_proposals(conn, account_id="account-alpha")
        props_beta = memories.list_proposals(conn, account_id="account-beta")
        assert len(props_alpha) == 1
        assert len(props_beta) == 0


def test_migration_017_applies(tmp_path) -> None:
    db_path = tmp_path / "mig_017_test.db"
    with open_app_state_db(db_path) as conn:
        applied = [r[0] for r in conn.execute("SELECT id FROM schema_migrations").fetchall()]
        assert "017_agentic_memory_retention" in applied

        # Verify idempotency: run again, newly applied is empty
        applied_second = apply_migrations(conn)
        assert "017_agentic_memory_retention" not in applied_second

        # Verify columns exist
        cols_prop = {r[1] for r in conn.execute("PRAGMA table_info(agentic_memory_proposals)").fetchall()}
        assert "expires_at" in cols_prop

        cols_item = {r[1] for r in conn.execute("PRAGMA table_info(agentic_memory_items)").fetchall()}
        assert "expires_at" in cols_item


def test_step_and_tool_call_trace_persistence(tmp_path) -> None:
    from risk_dashboard.modules.agentic_core.schemas.runs import AgentStep, ToolCallRecord

    db_path = tmp_path / "trace_repo_test.db"
    with open_app_state_db(db_path) as conn:
        repo = AgenticRunRepository()

        step1 = AgentStep(
            schema_version="1.0.0",
            step_id="step_test_0",
            run_id="run_trace_1",
            step_index=0,
            agent_id="supervisor",
            node_name="guard",
            status="completed",
            started_at="2026-09-08T00:00:00Z",
            completed_at="2026-09-08T00:00:01Z",
        )
        step2 = AgentStep(
            schema_version="1.0.0",
            step_id="step_test_1",
            run_id="run_trace_1",
            step_index=1,
            agent_id="supervisor",
            node_name="router",
            status="completed",
            started_at="2026-09-08T00:00:01Z",
            completed_at="2026-09-08T00:00:02Z",
        )
        repo.save_step(conn, step1)
        repo.save_step(conn, step2)

        tc = ToolCallRecord(
            schema_version="1.0.0",
            tool_call_id="tc_test_0",
            run_id="run_trace_1",
            account_id="acc_owner",
            tool_name="quant_risk_read_only",
            input_hash="hash123",
            status="success",
            evidence={"result": "ok"},
            latency_ms=45,
            created_at="2026-09-08T00:00:02Z",
        )
        repo.save_tool_call(conn, tc)

        # Query steps
        steps = repo.list_steps(conn, run_id="run_trace_1")
        assert len(steps) == 2
        assert steps[0].node_name == "guard"
        assert steps[1].node_name == "router"

        # Query tool calls with account scoping
        tcs_owner = repo.list_tool_calls(conn, run_id="run_trace_1", account_id="acc_owner")
        assert len(tcs_owner) == 1
        assert tcs_owner[0].tool_name == "quant_risk_read_only"
        assert tcs_owner[0].latency_ms == 45

        # Query tool calls with other account -> isolated
        tcs_other = repo.list_tool_calls(conn, run_id="run_trace_1", account_id="acc_other")
        assert len(tcs_other) == 0




