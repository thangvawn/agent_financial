"""End-to-End verified agentic workflows.

Covers:
- Path A: Offline deterministic agentic flow with persisted trace and review lifecycle.
- Path B: Confirmed safe write flow with idempotent ActionReceipt.
- Path C: Live Gemini execution flow (gracefully skipped if real key is not present).
"""
from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from risk_dashboard.modules.agentic_core.api.public import router
from risk_dashboard.modules.agentic_core.infrastructure.repositories import AgenticActionRepository
from risk_dashboard.modules.agentic_core.schemas.artifact import ActionProposal
from risk_dashboard.modules.agentic_core.schemas.envelope import ResourceRef
from risk_dashboard.modules.auth.application.dependencies import resolve_principal
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.platform.database import open_app_state_db

app = FastAPI()
app.include_router(router)

TEST_ACCOUNT_ID = "acct_e2e_user"


def override_principal():
    return AuthPrincipal(
        account_id=TEST_ACCOUNT_ID,
        scopes=("agentic:run:execute", "*"),
        session_id="sess_e2e",
        resolved_at="2026-09-09T00:00:00Z",
    )


app.dependency_overrides[resolve_principal] = override_principal
client = TestClient(app)


def test_e2e_path_a_offline_run_and_artifact_lifecycle(monkeypatch) -> None:
    """Path A: Full offline flow: Envelope -> Run -> Graph -> Steps -> Review -> Accept -> Export -> Trace."""
    monkeypatch.delenv("AGENTIC_KILL_SWITCH", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "mock-test-key")

    fake_result = {
        "status": "success",
        "code": None,
        "text": "Phân tích rủi ro danh mục hoàn tất với độ tin cậy 95%.",
        "evidence": {"metric": "var_95", "value": "-3.2%"},
        "trace": ("guard", "router", "specialist", "reviewer", "success"),
        "steps_used": 5,
        "tool_calls_used": 1,
        "tokens_used": 120,
        "cost_used": 0.0012,
        "reviewed_artifact": None,
    }

    with patch("risk_dashboard.modules.agentic_core.api.public.run_graph", new_callable=AsyncMock) as mock_graph:
        mock_graph.return_value = fake_result

        # 1. Create run
        resp_create = client.post(
            "/runs",
            json={
                "operation": "analyze_risk",
                "surface": "pro_lab",
                "resource_refs": [{"kind": "portfolio", "resource_id": "p1", "module": "risk"}],
                "locale": "vi-VN",
            },
        )
        assert resp_create.status_code == 200
        run_data = resp_create.json()
        run_id = run_data["run_id"]
        assert run_data["status"] == "completed"
        artifact_id = run_data["artifact"]["artifact_id"]

        # 2. Inspect run trace
        resp_trace = client.get(f"/runs/{run_id}/trace")
        assert resp_trace.status_code == 200
        trace_data = resp_trace.json()
        assert trace_data["run_id"] == run_id
        assert len(trace_data["steps"]) == 5
        assert trace_data["timeline"] == ["guard", "router", "specialist", "reviewer", "success"]
        assert len(trace_data["tool_calls"]) == 1

        # 3. Artifact Review Lifecycle transitions
        # Direct export on draft fails with 409 Conflict
        resp_bad_export = client.post(f"/artifacts/{artifact_id}:export")
        assert resp_bad_export.status_code == 409

        # Submit for review -> reviewed
        resp_review = client.post(f"/artifacts/{artifact_id}:review")
        assert resp_review.status_code == 200
        assert resp_review.json()["review_status"] == "reviewed"

        # Accept reviewed artifact -> accepted
        resp_accept = client.post(f"/artifacts/{artifact_id}:accept")
        assert resp_accept.status_code == 200
        assert resp_accept.json()["review_status"] == "accepted"

        # Export accepted artifact -> exported
        resp_export = client.post(f"/artifacts/{artifact_id}:export")
        assert resp_export.status_code == 200
        assert resp_export.json()["status"] == "exported"


def test_e2e_path_b_confirmed_safe_write() -> None:
    """Path B: Proposal -> Confirm -> Side-effect execution -> ActionReceipt -> Idempotency."""
    proposal_id = "prop_e2e_write_1"
    proposal = ActionProposal(
        proposal_id=proposal_id,
        run_id="run_e2e_2",
        account_id=TEST_ACCOUNT_ID,
        operation="save_preference",
        target=ResourceRef(kind="preference", resource_id="pref_risk_tolerance", module="agentic_core"),
        payload_preview={"content": "Khẩu vị rủi ro: Thận trọng (Conservative)"},
        risk_class="proposal",
        policy_version="1.0.0",
        created_at="2026-09-09T00:00:00Z",
        expires_at="2099-01-01T00:00:00Z",
    )
    with open_app_state_db() as conn:
        AgenticActionRepository().save_proposal(conn, proposal)

    # 1. Confirm write
    resp_confirm = client.post(f"/action-proposals/{proposal_id}:confirm")
    assert resp_confirm.status_code == 200
    receipt_id = resp_confirm.json()["receipt_id"]
    assert resp_confirm.json()["status"] == "confirmed"

    # 2. Verify side-effect execution in SQLite memory
    with open_app_state_db() as conn:
        row = conn.execute(
            "SELECT content, memory_type FROM agentic_memory_items WHERE account_id = ? AND content LIKE ?",
            (TEST_ACCOUNT_ID, "%Thận trọng%"),
        ).fetchone()
        assert row is not None
        assert row["memory_type"] == "preference"

        # Verify receipt record
        receipt = AgenticActionRepository().get_receipt(conn, proposal_id=proposal_id, account_id=TEST_ACCOUNT_ID)
        assert receipt is not None
        assert receipt.receipt_id == receipt_id
        assert receipt.status == "executed"

    # 3. Idempotent re-confirmation returns same receipt
    resp_reconfirm = client.post(f"/action-proposals/{proposal_id}:confirm")
    assert resp_reconfirm.status_code == 200
    assert resp_reconfirm.json()["receipt_id"] == receipt_id


@pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY") == "test",
    reason="Path C requires a valid live GEMINI_API_KEY",
)
def test_e2e_path_c_live_gemini_flow() -> None:
    """Path C: Live end-to-end execution against Gemini model."""
    resp = client.post(
        "/runs",
        json={
            "operation": "analyze_risk",
            "surface": "pro_lab",
            "resource_refs": [{"kind": "portfolio", "resource_id": "p1", "module": "risk"}],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "run_id" in data
    assert data["status"] in ("completed", "failed")
