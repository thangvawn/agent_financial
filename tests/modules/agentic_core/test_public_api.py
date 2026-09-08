import os
os.environ["GEMINI_API_KEY"] = "test"
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException
from risk_dashboard.modules.agentic_core.api.public import router, clear_run_store
from risk_dashboard.modules.agentic_core.infrastructure.repositories import AgenticActionRepository
from risk_dashboard.modules.agentic_core.schemas.artifact import ActionProposal
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


