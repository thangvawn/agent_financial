import os
os.environ["GEMINI_API_KEY"] = "test"
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException
from risk_dashboard.modules.agentic_core.api.public import router, clear_run_store
from risk_dashboard.modules.agentic_core.infrastructure.repositories import AgenticActionRepository
from risk_dashboard.modules.agentic_core.schemas.artifact import ActionProposal, AgentArtifact
from risk_dashboard.modules.agentic_core.schemas.envelope import ResourceRef
from risk_dashboard.modules.auth.application.dependencies import resolve_principal
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.platform.database import open_app_state_db

app = FastAPI()
app.include_router(router)

def override_principal_auth():
    return AuthPrincipal(
        account_id="acct_123",
        scopes=("agentic:run:execute",),
        session_id="sess_1",
        resolved_at="2026-09-07T00:00:00Z"
    )

def override_principal_no_auth():
    raise HTTPException(status_code=401, detail="Unauthorized")

app.dependency_overrides[resolve_principal] = override_principal_auth

client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup():
    clear_run_store()
    yield
    clear_run_store()

@pytest.fixture(autouse=True)
def mock_run_graph():
    with patch("risk_dashboard.modules.agentic_core.api.public.run_graph", new_callable=AsyncMock) as mock:
        mock.return_value = {"status": "success"}
        yield mock

def test_create_run_unauth():
    app.dependency_overrides[resolve_principal] = override_principal_no_auth
    resp = client.post("/runs", json={"operation": "test", "surface": "test"})
    assert resp.status_code == 401
    app.dependency_overrides[resolve_principal] = override_principal_auth

def test_create_run():
    resp = client.post("/runs", json={"operation": "test", "surface": "test"})
    assert resp.status_code == 200
    data = resp.json()
    assert "run_id" in data
    assert data["status"] in ["completed", "failed"]

def test_get_run():
    resp = client.post("/runs", json={"operation": "test", "surface": "test"})
    run_id = resp.json()["run_id"]
    
    resp_get = client.get(f"/runs/{run_id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["run_id"] == run_id

def test_cancel_run():
    resp = client.post("/runs", json={"operation": "test", "surface": "test"})
    run_id = resp.json()["run_id"]
    
    resp_cancel = client.post(f"/runs/{run_id}:cancel")
    assert resp_cancel.status_code == 200

def test_get_artifact():
    resp = client.post("/runs", json={"operation": "test", "surface": "test"})
    data = resp.json()
    assert data["artifact"] is not None
    artifact_id = data["artifact"]["artifact_id"]
    
    resp_art = client.get(f"/artifacts/{artifact_id}")
    assert resp_art.status_code == 200
    assert resp_art.json()["artifact_id"] == artifact_id

def test_confirm_action_proposal_not_found():
    resp = client.post("/action-proposals/prop_nonexistent:confirm")
    assert resp.status_code == 404

def test_confirm_and_reject_action_proposal():
    proposal = ActionProposal(
        proposal_id="prop_123",
        run_id="run_123",
        account_id="acct_123",
        operation="export_report",
        target=ResourceRef(kind="report", resource_id="r1", module="pro_lab"),
        payload_preview={"format": "pdf"},
        risk_class="proposal",
        policy_version="1.0.0",
        created_at="2026-09-07T00:00:00Z",
        expires_at="2099-01-01T00:00:00Z",
    )
    with open_app_state_db() as conn:
        AgenticActionRepository().save_proposal(conn, proposal)

    resp = client.post("/action-proposals/prop_123:confirm")
    assert resp.status_code == 200
    assert resp.json()["status"] == "confirmed"
    assert "receipt_id" in resp.json()

    # Idempotent re-confirm
    resp2 = client.post("/action-proposals/prop_123:confirm")
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "confirmed"

    # Reject another proposal
    proposal_reject = ActionProposal(
        proposal_id="prop_reject",
        run_id="run_123",
        account_id="acct_123",
        operation="delete_chart",
        target=ResourceRef(kind="report", resource_id="r2", module="pro_lab"),
        payload_preview={},
        risk_class="proposal",
        policy_version="1.0.0",
        created_at="2026-09-07T00:00:00Z",
        expires_at="2099-01-01T00:00:00Z",
    )
    with open_app_state_db() as conn:
        AgenticActionRepository().save_proposal(conn, proposal_reject)

    resp_rej = client.post("/action-proposals/prop_reject:reject")
    assert resp_rej.status_code == 200
    assert resp_rej.json()["status"] == "rejected"


def test_confirm_action_proposal_expired():
    proposal = ActionProposal(
        proposal_id="prop_expired",
        run_id="run_123",
        account_id="acct_123",
        operation="export_report",
        target=ResourceRef(kind="report", resource_id="r1", module="pro_lab"),
        payload_preview={"format": "pdf"},
        risk_class="proposal",
        policy_version="1.0.0",
        created_at="2020-01-01T00:00:00Z",
        expires_at="2020-01-02T00:00:00Z",
    )
    with open_app_state_db() as conn:
        AgenticActionRepository().save_proposal(conn, proposal)

    resp = client.post("/action-proposals/prop_expired:confirm")
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()


def test_confirm_action_proposal_cross_account():
    proposal = ActionProposal(
        proposal_id="prop_other_account",
        run_id="run_other",
        account_id="acct_other",
        operation="export_report",
        target=ResourceRef(kind="report", resource_id="r1", module="pro_lab"),
        payload_preview={"format": "pdf"},
        risk_class="proposal",
        policy_version="1.0.0",
        created_at="2026-09-07T00:00:00Z",
        expires_at="2099-01-01T00:00:00Z",
    )
    with open_app_state_db() as conn:
        AgenticActionRepository().save_proposal(conn, proposal)

    # Current principal is acct_123, cannot access acct_other's proposal
    resp = client.post("/action-proposals/prop_other_account:confirm")
    assert resp.status_code == 404


def test_artifact_lifecycle_transitions():
    from risk_dashboard.modules.agentic_core.infrastructure.repositories import AgenticArtifactRepository

    artifact = AgentArtifact(
        artifact_id="art_lifecycle_1",
        artifact_type="socratic_hint",
        domain="learning",
        account_id="acct_123",
        authoring_run_id="run_123",
        review_status="draft",
        version=1,
        created_at="2026-09-08T00:00:00Z",
    )
    with open_app_state_db() as conn:
        AgenticArtifactRepository().save(conn, artifact)

    # Cannot export unreviewed draft artifact
    resp_exp_draft = client.post("/artifacts/art_lifecycle_1:export")
    assert resp_exp_draft.status_code == 409

    # Submit for review
    resp_rev = client.post("/artifacts/art_lifecycle_1:review")
    assert resp_rev.status_code == 200
    assert resp_rev.json()["review_status"] == "reviewed"

    # Accept
    resp_acc = client.post("/artifacts/art_lifecycle_1:accept")
    assert resp_acc.status_code == 200
    assert resp_acc.json()["review_status"] == "accepted"

    # Idempotent accept
    resp_acc2 = client.post("/artifacts/art_lifecycle_1:accept")
    assert resp_acc2.status_code == 200

    # Export accepted artifact
    resp_exp = client.post("/artifacts/art_lifecycle_1:export")
    assert resp_exp.status_code == 200
    assert resp_exp.json()["status"] == "exported"


def test_artifact_lifecycle_expired():
    from risk_dashboard.modules.agentic_core.infrastructure.repositories import AgenticArtifactRepository

    artifact = AgentArtifact(
        artifact_id="art_expired_1",
        artifact_type="socratic_hint",
        domain="learning",
        account_id="acct_123",
        authoring_run_id="run_123",
        review_status="draft",
        version=1,
        created_at="2020-01-01T00:00:00Z",
        expires_at="2020-01-02T00:00:00Z",
    )
    with open_app_state_db() as conn:
        AgenticArtifactRepository().save(conn, artifact)

    # Review or accept or export on expired artifact fails
    resp_rev = client.post("/artifacts/art_expired_1:review")
    assert resp_rev.status_code == 409

    resp_acc = client.post("/artifacts/art_expired_1:accept")
    assert resp_acc.status_code == 409

    resp_exp = client.post("/artifacts/art_expired_1:export")
    assert resp_exp.status_code == 409


def test_action_service_blocks_forbidden():
    proposal = ActionProposal(
        proposal_id="prop_forbidden_1",
        run_id="run_123",
        account_id="acct_123",
        operation="direct_db_drop",
        target=ResourceRef(kind="database", resource_id="app_state", module="platform"),
        payload_preview={"sql": "DROP TABLE users"},
        risk_class="forbidden",
        policy_version="1.0.0",
        created_at="2026-09-08T00:00:00Z",
        expires_at="2099-01-01T00:00:00Z",
    )
    with open_app_state_db() as conn:
        AgenticActionRepository().save_proposal(conn, proposal)

    resp = client.post("/action-proposals/prop_forbidden_1:confirm")
    assert resp.status_code == 403
    assert "forbidden" in resp.json()["detail"].lower()

    with open_app_state_db() as conn:
        receipt = AgenticActionRepository().get_receipt(conn, proposal_id="prop_forbidden_1", account_id="acct_123")
        assert receipt is not None
        assert receipt.status == "failed"
        assert receipt.error_code == "FORBIDDEN_ACTION_BLOCKED"


def test_action_service_rejection_conflict():
    proposal = ActionProposal(
        proposal_id="prop_reject_conflict",
        run_id="run_123",
        account_id="acct_123",
        operation="sample_action",
        target=ResourceRef(kind="report", resource_id="r1", module="pro_lab"),
        payload_preview={},
        risk_class="proposal",
        policy_version="1.0.0",
        created_at="2026-09-08T00:00:00Z",
        expires_at="2099-01-01T00:00:00Z",
    )
    with open_app_state_db() as conn:
        AgenticActionRepository().save_proposal(conn, proposal)

    resp_rej = client.post("/action-proposals/prop_reject_conflict:reject")
    assert resp_rej.status_code == 200

    # Trying to confirm rejected proposal causes 409 Conflict
    resp_conf = client.post("/action-proposals/prop_reject_conflict:confirm")
    assert resp_conf.status_code == 409


def test_action_service_executes_real_preference():
    proposal = ActionProposal(
        proposal_id="prop_pref_real",
        run_id="run_123",
        account_id="acct_123",
        operation="save_preference",
        target=ResourceRef(kind="user_preference", resource_id="pref_theme", module="agentic_core"),
        payload_preview={"content": "VN30 index tracking preference"},
        risk_class="proposal",
        policy_version="1.0.0",
        created_at="2026-09-08T00:00:00Z",
        expires_at="2099-01-01T00:00:00Z",
    )
    with open_app_state_db() as conn:
        AgenticActionRepository().save_proposal(conn, proposal)

    resp = client.post("/action-proposals/prop_pref_real:confirm")
    assert resp.status_code == 200

    with open_app_state_db() as conn:
        row = conn.execute(
            "SELECT content, memory_type FROM agentic_memory_items WHERE account_id = 'acct_123' AND content = 'VN30 index tracking preference'"
        ).fetchone()
        assert row is not None
        assert row["memory_type"] == "preference"


def test_kill_switch_blocks_new_runs(monkeypatch):
    monkeypatch.setenv("AGENTIC_KILL_SWITCH", "true")

    resp = client.post(
        "/runs",
        json={
            "operation": "analyze_risk",
            "surface": "chat",
            "resource_refs": [{"kind": "portfolio", "resource_id": "p1", "module": "risk"}],
        },
    )
    assert resp.status_code == 503
    assert "kill switch" in resp.json()["detail"].lower()


def test_run_inspector_trace_timeline(monkeypatch):
    monkeypatch.delenv("AGENTIC_KILL_SWITCH", raising=False)

    fake_result = {
        "status": "success",
        "code": None,
        "text": "Analysis complete",
        "evidence": {"metric": "var_95"},
        "trace": ("guard", "router", "specialist", "reviewer", "success"),
        "steps_used": 5,
        "tool_calls_used": 1,
        "tokens_used": 100,
        "cost_used": 0.001,
        "reviewed_artifact": None,
    }

    with patch("risk_dashboard.modules.agentic_core.api.public.run_graph", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = fake_result
        resp_run = client.post(
            "/runs",
            json={
                "operation": "analyze_risk",
                "surface": "chat",
                "resource_refs": [{"kind": "portfolio", "resource_id": "p1", "module": "risk"}],
            },
        )
        assert resp_run.status_code == 200
        run_id = resp_run.json()["run_id"]

    # Now inspect trace
    resp_trace = client.get(f"/runs/{run_id}/trace")
    assert resp_trace.status_code == 200
    trace_data = resp_trace.json()
    assert trace_data["run_id"] == run_id
    assert trace_data["status"] == "completed"
    assert len(trace_data["steps"]) == 5
    assert trace_data["timeline"] == ["guard", "router", "specialist", "reviewer", "success"]
    assert len(trace_data["tool_calls"]) == 1
    assert trace_data["tool_calls"][0]["tool_name"] in ("quant.explain_risk", "quant_risk_read_only")





