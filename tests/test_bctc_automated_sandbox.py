from __future__ import annotations

import hashlib
import json
import logging
import os
import pytest
from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.auth.application.services import RegisterAccount
from risk_dashboard.modules.auth.infrastructure.sqlite import (
    SqliteAccountRepository,
    SqliteAccountSessionRepository,
)
from risk_dashboard.platform.database import clear_db_path_cache


@pytest.fixture
def test_client(tmp_path, monkeypatch):
    """Isolated database and test client fixture with 2 registered user accounts."""
    db_path = str(tmp_path / "app_state.db")
    monkeypatch.setenv("RISK_DASHBOARD_APP_STATE_DB", db_path)
    clear_db_path_cache()

    accounts = SqliteAccountRepository()
    sessions = SqliteAccountSessionRepository()

    acc_a, sess_a = RegisterAccount(accounts=accounts, sessions=sessions).execute(
        name="User A",
        email=f"usera-{tmp_path.name}@example.com",
        password="password-123",
    )
    acc_b, sess_b = RegisterAccount(accounts=accounts, sessions=sessions).execute(
        name="User B",
        email=f"userb-{tmp_path.name}@example.com",
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
# PHASE 1: Infrastructure & Health Baseline
# ==============================================================================

def test_phase1_bctc_health_baseline(test_client):
    """Xác nhận service BCTC Agent hoạt động, database ok, đăng ký đủ 6 tools."""
    client = test_client["client"]

    # Endpoint chuẩn bctc-agent
    resp_agent = client.get("/api/v1/public/bctc/agent/health/bctc-agent")
    assert resp_agent.status_code == 200, f"Expected 200, got {resp_agent.status_code}: {resp_agent.text}"
    data_agent = resp_agent.json()

    assert data_agent["status"] == "healthy", f"Expected healthy, got {data_agent['status']}"
    assert "checks" in data_agent
    checks = data_agent["checks"]
    assert checks["tool_registry"] == "ok"
    assert checks["bctc_tools_registered"] == 6, f"Expected 6 tools, got {checks['bctc_tools_registered']}"
    assert checks["database"] == "ok"
    assert checks["feature_flag"] == "enabled"

    # Alias endpoint router health
    resp_alias = client.get("/api/v1/public/bctc/agent/health")
    assert resp_alias.status_code == 200
    assert resp_alias.json()["status"] == "healthy"
    assert resp_alias.json()["checks"]["bctc_tools_registered"] == 6


# ==============================================================================
# PHASE 2: Security & IDOR Red Teaming (P0 Priority)
# ==============================================================================

def test_phase2_bctc_idor_memo_isolation(test_client):
    """Kiểm chứng cô lập đa tenant: User B truy cập memo của User A PHẢI trả về 404 Not Found."""
    client = test_client["client"]
    headers_a = test_client["headers_a"]
    headers_b = test_client["headers_b"]

    # Bước 2.1: User A tạo Evidence Memo
    create_resp = client.post(
        "/api/v1/public/bctc/agent/memos",
        headers=headers_a,
        json={
            "subject": "Biên lợi nhuận gộp FPT Q3/2024",
            "scope": "public",
            "report_refs": [
                {
                    "report_id": "report:fpt",
                    "revision_id": "rev_2024q3_vndirect",
                    "period": "2024Q3",
                    "source": "vndirect",
                    "fetched_at": "2026-09-01T00:00:00Z",
                }
            ],
            "evidence_rows": [
                {
                    "claim_ref": "revenue",
                    "amount": {
                        "value": 15000.0,
                        "unit": "VND_bn",
                        "provenance": {
                            "report_id": "report:fpt",
                            "revision_id": "rev_2024q3_vndirect",
                            "period": "2024Q3",
                            "source": "vndirect",
                            "fetched_at": "2026-09-01T00:00:00Z",
                        },
                    },
                }
            ],
        },
    )
    assert create_resp.status_code in (200, 201), f"Create memo failed: {create_resp.text}"
    memo_id = create_resp.json()["memo_id"]
    assert memo_id.startswith("memo_")

    # Xác nhận User A đọc được memo chính chủ
    get_a = client.get(f"/api/v1/public/bctc/agent/memos/{memo_id}", headers=headers_a)
    assert get_a.status_code == 200
    assert get_a.json()["memo_id"] == memo_id

    # Bước 2.2: Red Team - User B cố gắng đọc Memo của User A -> BẮT BUỘC 404 (Không được là 403 hoặc 200)
    get_b = client.get(f"/api/v1/public/bctc/agent/memos/{memo_id}", headers=headers_b)
    assert get_b.status_code == 404, (
        f"IDOR Violation! Expected 404 Not Found (Anti-Oracle Guard), but got {get_b.status_code}"
    )

    # Bước 2.3: Red Team - User B cố gắng xóa Memo của User A -> BẮT BUỘC 404
    del_b = client.delete(f"/api/v1/public/bctc/agent/memos/{memo_id}", headers=headers_b)
    assert del_b.status_code == 404, (
        f"IDOR Violation! Expected 404 Not Found on DELETE, but got {del_b.status_code}"
    )

    # Bước 2.4: User B list memos -> memo của User A không xuất hiện
    list_b = client.get("/api/v1/public/bctc/agent/memos", headers=headers_b)
    assert list_b.status_code == 200
    memos_b = list_b.json().get("memos", [])
    assert all(m["memo_id"] != memo_id for m in memos_b), "User A's memo leaked into User B's memo list!"


# ==============================================================================
# PHASE 3: Core Agent Workflow & Grounding Gate
# ==============================================================================

def test_phase3_bctc_calculate_ratio_provenance(test_client):
    """Kiểm tra workflow tính toán chỉ số kèm chuỗi nguồn gốc và zero hardcode."""
    client = test_client["client"]
    headers_a = test_client["headers_a"]

    # Bước 3.1: Resolve Report
    resp_rep = client.post(
        "/api/v1/public/bctc/agent/tools/bctc.resolve_report:invoke",
        headers=headers_a,
        json={"tool_id": "bctc.resolve_report", "input": {"ticker": "FPT"}},
    )
    assert resp_rep.status_code == 200
    rep_output = resp_rep.json()["output"]
    report_id = rep_output["report_id"]
    revision_id = rep_output["revision_id"]
    assert report_id is not None
    assert revision_id is not None

    # Bước 3.2: Calculate Ratio với input hợp lệ
    resp_ratio = client.post(
        "/api/v1/public/bctc/agent/tools/bctc.calculate_ratio:invoke",
        headers=headers_a,
        json={
            "tool_id": "bctc.calculate_ratio",
            "input": {
                "report_id": report_id,
                "revision_id": revision_id,
                "period": "2024Q3",
                "formula_id": "gross_margin",
            },
        },
    )
    assert resp_ratio.status_code == 200
    assert resp_ratio.headers.get("Cache-Control") == "no-store"
    ratio_output = resp_ratio.json()["output"]

    assert ratio_output["formula_id"] == "gross_margin"
    assert "result" in ratio_output
    assert ratio_output["result"]["provenance"] is not None

    # Zero Hardcode Check: 52618 không xuất hiện trong payload
    serialized_ratio = json.dumps(resp_ratio.json())
    assert "52618" not in serialized_ratio, "Found hardcoded value 52618 in calculate_ratio response!"


def test_phase3_bctc_grounding_gate_rejection(test_client):
    """Cổng Grounding Gate (NumericReviewer) chặn các claim không có bằng chứng với 422 GROUNDING_FAILED."""
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
            "test_inject_unsupported_claim": True,
        },
    )
    assert resp.status_code == 422, f"Expected 422 GROUNDING_FAILED, got {resp.status_code}"
    err = resp.json()["error"]
    assert err["code"] == "GROUNDING_FAILED"
    assert "unsupported_claims" in err
    assert len(err["unsupported_claims"]) > 0


# ==============================================================================
# PHASE 4: Frontend API Contracts & HITL
# ==============================================================================

def test_phase4_bctc_memo_creation_contract(test_client):
    """Xác minh hợp đồng schema của POST /memos cho HITL Drawer và Idempotency-Key."""
    client = test_client["client"]
    headers_a = test_client["headers_a"]

    memo_payload = {
        "subject": "Phân tích biên lợi nhuận FPT 2024Q3",
        "scope": "public",
        "report_refs": [
            {
                "report_id": "report:fpt",
                "revision_id": "rev_2024q3_vndirect",
                "period": "2024Q3",
                "source": "vndirect",
                "fetched_at": "2026-09-01T00:00:00Z",
            }
        ],
        "evidence_rows": [
            {
                "claim_ref": "revenue",
                "amount": {
                    "value": 15000.0,
                    "unit": "VND_bn",
                    "provenance": {
                        "report_id": "report:fpt",
                        "revision_id": "rev_2024q3_vndirect",
                        "period": "2024Q3",
                        "source": "vndirect",
                        "fetched_at": "2026-09-01T00:00:00Z",
                    },
                },
            }
        ],
    }

    # Test với Idempotency-Key
    idem_key = "hitl-user-a-memo-1"
    headers_with_idem = {**headers_a, "Idempotency-Key": idem_key}

    # Gọi lần 1
    resp1 = client.post("/api/v1/public/bctc/agent/memos", headers=headers_with_idem, json=memo_payload)
    assert resp1.status_code in (200, 201)
    data1 = resp1.json()

    # Kiểm tra các trường bắt buộc cho Frontend HITL UI
    assert "memo_id" in data1
    assert "created_at" in data1
    assert data1["subject"] == memo_payload["subject"]
    assert data1["scope"] == memo_payload["scope"]
    assert len(data1["evidence_rows"]) == 1

    # Gọi lần 2 với cùng Idempotency-Key -> phải trả về đúng memo đã tạo (idempotent)
    resp2 = client.post("/api/v1/public/bctc/agent/memos", headers=headers_with_idem, json=memo_payload)
    assert resp2.status_code in (200, 201)
    data2 = resp2.json()
    assert data2["memo_id"] == data1["memo_id"]


# ==============================================================================
# PHASE 5: Observability & Log PII Audit
# ==============================================================================

def test_phase5_bctc_logging_pii_compliance(test_client, caplog):
    """Xác nhận logging chuẩn JSON, chứa account_id_hash, KHÔNG leak raw account_id hoặc 52618."""
    client = test_client["client"]
    headers_a = test_client["headers_a"]
    acc_a_id = test_client["acc_a"].account_id
    expected_hash = hashlib.sha256(acc_a_id.encode("utf-8")).hexdigest()[:12]

    with caplog.at_level(logging.INFO):
        # 1. Gọi Tool invocation
        resp_tool = client.post(
            "/api/v1/public/bctc/agent/tools/bctc.resolve_report:invoke",
            headers=headers_a,
            json={"tool_id": "bctc.resolve_report", "input": {"ticker": "FPT"}},
        )
        assert resp_tool.status_code == 200

        # 2. Tạo Memo
        resp_memo = client.post(
            "/api/v1/public/bctc/agent/memos",
            headers=headers_a,
            json={
                "subject": "Audit PII Logging Subject",
                "scope": "public",
                "report_refs": [],
                "evidence_rows": [],
            },
        )
        assert resp_memo.status_code in (200, 201)

    # Thẩm định log records
    records = caplog.records

    # Check tool.completed event
    tool_events = [r for r in records if getattr(r, "event", None) == "bctc.tool.completed"]
    assert len(tool_events) >= 1
    t_ev = tool_events[-1]
    assert getattr(t_ev, "account_id_hash", None) == expected_hash
    assert getattr(t_ev, "duration_ms", None) is not None
    assert getattr(t_ev, "status", None) == "success"

    # Check memo.created event
    memo_events = [r for r in records if getattr(r, "event", None) == "bctc.evidence_memo.created"]
    assert len(memo_events) >= 1
    m_ev = memo_events[-1]
    assert getattr(m_ev, "account_id_hash", None) == expected_hash
    assert getattr(m_ev, "memo_id", None) is not None

    # Zero PII & Zero 52618 Leak check trên toàn bộ log messages
    for rec in records:
        log_msg = rec.getMessage()
        # Raw account_id không được xuất hiện trực tiếp trong log message
        assert acc_a_id not in log_msg, f"PII Leak! Raw account_id '{acc_a_id}' found in log message: {log_msg}"
        assert "52618" not in log_msg, f"Found hardcoded 52618 in log message: {log_msg}"

