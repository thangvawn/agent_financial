from __future__ import annotations

import json
import os
import pytest
from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.agentic_core.application.tool_registry import get_default_tool_registry
from risk_dashboard.modules.agentic_core.application.skill_router import SkillRouter
from risk_dashboard.modules.auth.application.services import RegisterAccount
from risk_dashboard.modules.auth.infrastructure.sqlite import (
    SqliteAccountRepository,
    SqliteAccountSessionRepository,
)
from risk_dashboard.platform.database import clear_db_path_cache


@pytest.fixture
def test_client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "app_state.db")
    monkeypatch.setenv("RISK_DASHBOARD_APP_STATE_DB", db_path)
    clear_db_path_cache()

    accounts = SqliteAccountRepository()
    sessions = SqliteAccountSessionRepository()

    acc_a, sess_a = RegisterAccount(accounts=accounts, sessions=sessions).execute(
        name="User A",
        email=f"a-{tmp_path.name}@example.com",
        password="password-123",
    )
    acc_b, sess_b = RegisterAccount(accounts=accounts, sessions=sessions).execute(
        name="User B",
        email=f"b-{tmp_path.name}@example.com",
        password="password-456",
    )

    client = TestClient(app)
    return {
        "client": client,
        "acc_a": acc_a,
        "sess_a": sess_a,
        "headers_a": {"Authorization": f"Bearer {sess_a.session_id}"},
        "acc_b": acc_b,
        "sess_b": sess_b,
        "headers_b": {"Authorization": f"Bearer {sess_b.session_id}"},
        "tmp_path": tmp_path,
    }


# ==============================================================================
# GÓI P0: KHAI THÔNG LÕI & BẢO MẬT (S1, S2, S3)
# ==============================================================================

def test_tool_registry_contains_all_bctc_tools():
    """G3: Tool registry trung tâm phải chứa đầy đủ 6 BCTC tools."""
    registry = get_default_tool_registry()
    expected_tools = [
        "bctc.resolve_report",
        "bctc.resolve_line_item",
        "bctc.compare_periods",
        "bctc.calculate_ratio",
        "bctc.trace_provenance",
        "bctc.build_evidence_table",
    ]
    for tid in expected_tools:
        manifest = registry.get(tid)
        assert manifest is not None, f"Tool '{tid}' must be registered in ToolRegistry"


def test_no_stub_52618_in_domain_tools():
    """G4: Domain tools của agentic_core không được chứa stub trả số hardcode 52618."""
    from risk_dashboard.modules.agentic_core.infrastructure import domain_tools
    import inspect
    src = inspect.getsource(domain_tools)
    assert "52618" not in src, "Stub 52618 must be removed from domain_tools.py"


def test_skill_router_resolves_bctc_skills():
    """G3 & S2: SkillRouter phải giải quyết đúng 5 BCTC skills đến real tools."""
    bctc_skills = [
        ("bctc.explain_line_item.v1", "bctc.resolve_line_item"),
        ("bctc.compare_periods.v1", "bctc.compare_periods"),
        ("bctc.ratio_walkthrough.v1", "bctc.calculate_ratio"),
        ("bctc.earnings_quality_review.v1", "bctc.build_evidence_table"),
        ("bctc.research_checklist.v1", "bctc.trace_provenance"),
    ]
    for skill_id, expected_tool_id in bctc_skills:
        tool = SkillRouter.resolve_skill(skill_id)
        assert hasattr(tool, "manifest"), f"Resolved tool for {skill_id} must have manifest"
        assert tool.manifest.tool_id == expected_tool_id, f"Skill {skill_id} must map to {expected_tool_id}"


def test_upload_analysis_unauthenticated_cannot_access_user_upload(test_client, monkeypatch):
    """G2: Client unauthenticated không được phép phân tích file upload thuộc về User A (404)."""
    client = test_client["client"]
    headers_a = test_client["headers_a"]
    tmp_path = test_client["tmp_path"]

    uploads_dir = str(tmp_path / "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    monkeypatch.setenv("RISK_DASHBOARD_FINANCIAL_UPLOADS_DIR", uploads_dir)

    csv_content = b"ticker,year,quarter,revenue,net_income\nTESTUPLOAD,2024,Q3,1000,100\n"
    upload_resp = client.post(
        "/financials/upload",
        headers=headers_a,
        data={"ticker": "TESTUPLOAD", "report_type": "auto", "period": "2024Q3"},
        files={"file": ("test.csv", csv_content, "text/csv")},
    )
    assert upload_resp.status_code == 200
    upload_id = upload_resp.json()["upload_id"]

    # Unauthenticated client attempts to analyze User A's upload -> must be 404
    resp = client.post(f"/financials/uploads/{upload_id}/analyze")
    assert resp.status_code == 404, f"Expected 404 for unauthenticated access to user upload, got {resp.status_code}"


def test_upload_analysis_enforces_ownership(test_client, monkeypatch):
    """G2: User B không được phép phân tích file upload thuộc về User A (404/403)."""
    client = test_client["client"]
    headers_a = test_client["headers_a"]
    headers_b = test_client["headers_b"]
    tmp_path = test_client["tmp_path"]

    uploads_dir = str(tmp_path / "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    monkeypatch.setenv("RISK_DASHBOARD_FINANCIAL_UPLOADS_DIR", uploads_dir)

    # User A uploads a valid csv file
    csv_content = b"ticker,year,quarter,revenue,net_income\nTESTUPLOAD,2024,Q3,1000,100\n"
    upload_resp = client.post(
        "/financials/upload",
        headers=headers_a,
        data={"ticker": "TESTUPLOAD", "report_type": "auto", "period": "2024Q3"},
        files={"file": ("test.csv", csv_content, "text/csv")},
    )
    assert upload_resp.status_code == 200, f"Upload failed: {upload_resp.text}"
    upload_id = upload_resp.json()["upload_id"]

    # User B attempts to analyze User A's upload -> must be 404 (or 403)
    resp_b = client.post(f"/financials/uploads/{upload_id}/analyze", headers=headers_b)
    assert resp_b.status_code in (403, 404), f"User B analyzing User A's upload must be 403 or 404, got {resp_b.status_code}"

    # User A analyzes own upload -> should succeed
    resp_a = client.post(f"/financials/uploads/{upload_id}/analyze", headers=headers_a)
    assert resp_a.status_code == 200, f"User A analyzing own upload should succeed, got {resp_a.status_code}"


# ==============================================================================
# GÓI P1: XÂY DỰNG HTTP AGENT API SURFACE (S4, S5, S6, S7)
# ==============================================================================

def test_agent_tool_invoke_endpoint(test_client):
    """G1 & S4: POST /api/v1/public/bctc/agent/tools/{tool_id}:invoke."""
    client = test_client["client"]
    headers_a = test_client["headers_a"]

    resp = client.post(
        "/api/v1/public/bctc/agent/tools/bctc.calculate_ratio:invoke",
        headers=headers_a,
        json={
            "input": {
                "report_id": "report:fpt",
                "revision_id": "rev_test",
                "period": "2024Q3",
                "formula_id": "gross_margin",
            }
        },
    )
    assert resp.status_code == 200, f"Tool invoke failed: {resp.text}"
    data = resp.json()
    assert data["tool_id"] == "bctc.calculate_ratio"
    assert "output" in data
    assert data["output"]["formula_id"] == "gross_margin"


def test_create_and_get_run_endpoint(test_client):
    """G1 & S5: POST /runs và GET /runs/{run_id}."""
    client = test_client["client"]
    headers_a = test_client["headers_a"]

    resp = client.post(
        "/api/v1/public/bctc/agent/runs",
        headers=headers_a,
        json={
            "skill_id": "bctc.explain_line_item.v1",
            "ticker": "FPT",
            "periods": ["2024Q3"],
            "line_item": "revenue",
        },
    )
    assert resp.status_code in (200, 201, 202), f"Create run failed: {resp.text}"
    run_id = resp.json()["run_id"]

    get_resp = client.get(f"/api/v1/public/bctc/agent/runs/{run_id}", headers=headers_a)
    assert get_resp.status_code == 200
    run_data = get_resp.json()
    assert run_data["run_id"] == run_id
    assert run_data["status"] in ("queued", "running", "completed", "awaiting_review")


def test_numeric_reviewer_blocks_unsupported_claims(test_client):
    """G4 & S6: Response có claim bịa đặt phải bị chặn với 422 GROUNDING_FAILED."""
    client = test_client["client"]
    headers_a = test_client["headers_a"]

    # Post run with an ungrounded claim injected
    resp = client.post(
        "/api/v1/public/bctc/agent/runs",
        headers=headers_a,
        json={
            "skill_id": "bctc.explain_line_item.v1",
            "ticker": "FPT",
            "periods": ["2024Q3"],
            "line_item": "revenue",
            "test_inject_unsupported_claim": True,
        },
    )
    assert resp.status_code == 422, f"Expected 422 GROUNDING_FAILED, got {resp.status_code}"
    err = resp.json()["error"]
    assert err["code"] == "GROUNDING_FAILED"


def test_memo_crud_and_ownership(test_client):
    """G5 & S7: CRUD Evidence Memo có ownership check."""
    client = test_client["client"]
    headers_a = test_client["headers_a"]
    headers_b = test_client["headers_b"]

    # 1. User A creates memo
    create_resp = client.post(
        "/api/v1/public/bctc/agent/memos",
        headers=headers_a,
        json={
            "subject": "Biên lợi nhuận gộp FPT Q3/2024",
            "scope": "public",
            "report_refs": [{
                "report_id": "report:fpt",
                "revision_id": "rev_123",
                "period": "2024Q3",
                "source": "vndirect",
                "fetched_at": "2026-09-01T00:00:00Z",
            }],
            "evidence_rows": [{
                "claim_ref": "revenue",
                "amount": {
                    "value": 52618.0,
                    "unit": "VND_bn",
                    "provenance": {
                        "report_id": "report:fpt",
                        "revision_id": "rev_123",
                        "period": "2024Q3",
                        "source": "vndirect",
                        "fetched_at": "2026-09-01T00:00:00Z",
                    }
                }
            }],
        },
    )
    assert create_resp.status_code in (200, 201), f"Create memo failed: {create_resp.text}"
    memo_id = create_resp.json()["memo_id"]

    # 2. User A can retrieve memo
    get_a = client.get(f"/api/v1/public/bctc/agent/memos/{memo_id}", headers=headers_a)
    assert get_a.status_code == 200
    assert get_a.json()["memo_id"] == memo_id

    # 3. User B CANNOT retrieve User A's memo -> 404
    get_b = client.get(f"/api/v1/public/bctc/agent/memos/{memo_id}", headers=headers_b)
    assert get_b.status_code == 404

    # 4. User B lists memos -> User A's memo must not be included
    list_b = client.get("/api/v1/public/bctc/agent/memos", headers=headers_b)
    assert list_b.status_code == 200
    memos_b = list_b.json().get("memos", [])
    assert all(m["memo_id"] != memo_id for m in memos_b)


# ==============================================================================
# GÓI P2: VẬN HÀNH & GIÁM SÁT (S8, S9)
# ==============================================================================

def test_bctc_agent_health_endpoint(test_client):
    """G6 & S9: GET /api/v1/public/bctc/agent/health and /api/v1/public/bctc/agent/health/bctc-agent."""
    client = test_client["client"]
    for path in ("/api/v1/public/bctc/agent/health", "/api/v1/public/bctc/agent/health/bctc-agent"):
        resp = client.get(path)
        assert resp.status_code == 200, f"Health check failed for {path}: {resp.text}"
        data = resp.json()
        assert data["status"] in ("healthy", "degraded")
        assert "checks" in data
        assert "tool_registry" in data["checks"]
        assert data["checks"]["bctc_tools_registered"] == 6


def test_bctc_metrics_and_account_hash_logging(test_client, caplog):
    """G8 & S8: Logging must not leak raw account_id, metrics increment properly."""
    import logging
    import hashlib
    from risk_dashboard.modules.financials_product.metrics import BCTC_TOOL_CALLS_TOTAL

    client = test_client["client"]
    headers_a = test_client["headers_a"]
    acc_a_id = test_client["acc_a"].account_id
    expected_hash = hashlib.sha256(acc_a_id.encode("utf-8")).hexdigest()[:12]

    with caplog.at_level(logging.INFO):
        resp = client.post(
            "/api/v1/public/bctc/agent/tools/bctc.resolve_report:invoke",
            headers=headers_a,
            json={
                "tool_id": "bctc.resolve_report",
                "input": {
                    "ticker": "FPT",
                },
            },
        )
        assert resp.status_code == 200

    # Ensure log record has account_id_hash
    tool_completed_records = [
        rec for rec in caplog.records if getattr(rec, "event", None) == "bctc.tool.completed"
    ]
    assert len(tool_completed_records) >= 1
    rec = tool_completed_records[-1]
    assert getattr(rec, "account_id_hash", None) == expected_hash
    assert getattr(rec, "tool_id", None) == "bctc.resolve_report"
    assert getattr(rec, "status", None) == "success"
    assert getattr(rec, "duration_ms", None) is not None
    # Ensure raw account_id is not in log record attribute
    assert not hasattr(rec, "raw_account_id")

