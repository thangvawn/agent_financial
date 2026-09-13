from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from risk_dashboard.api.main import app
from risk_dashboard.modules.auth.application.services import RegisterAccount
from risk_dashboard.modules.auth.infrastructure.sqlite import (
    SqliteAccountConsentRepository,
    SqliteAccountRepository,
    SqliteAccountSessionRepository,
)
from risk_dashboard.platform.database import clear_db_path_cache


@pytest.fixture
def idor_fixture(tmp_path, monkeypatch):
    db_path = str(tmp_path / "app_state.db")
    monkeypatch.setenv("RISK_DASHBOARD_APP_STATE_DB", db_path)
    clear_db_path_cache()

    accounts = SqliteAccountRepository()
    sessions = SqliteAccountSessionRepository()

    # User A
    acc_a, sess_a = RegisterAccount(accounts=accounts, sessions=sessions).execute(
        name="User Alpha",
        email=f"alpha-{tmp_path.name}@example.com",
        password="password-alpha-123",
    )

    # User B
    acc_b, sess_b = RegisterAccount(accounts=accounts, sessions=sessions).execute(
        name="User Beta",
        email=f"beta-{tmp_path.name}@example.com",
        password="password-beta-123",
    )

    client = TestClient(app)
    return {
        "acc_a": acc_a,
        "sess_a": sess_a,
        "headers_a": {"Authorization": f"Bearer {sess_a.session_id}"},
        "acc_b": acc_b,
        "sess_b": sess_b,
        "headers_b": {"Authorization": f"Bearer {sess_b.session_id}"},
        "client": client,
    }


def test_idor_surface_agentic_runs_isolation(idor_fixture):
    from datetime import datetime, timezone
    from risk_dashboard.modules.agentic_core.infrastructure.repositories import AgenticRunRepository
    from risk_dashboard.modules.agentic_core.schemas.runs import AgentRun
    from risk_dashboard.platform.database import open_app_state_db

    client = idor_fixture["client"]
    acc_a = idor_fixture["acc_a"]
    headers_b = idor_fixture["headers_b"]

    # Seed run for User A
    run_repo = AgenticRunRepository()
    run_id_a = "run_alpha_secret_999"
    now_iso = datetime.now(timezone.utc).isoformat()
    record_a = AgentRun(
        run_id=run_id_a,
        account_id=acc_a.account_id,
        surface="research",
        status="completed",
        correlation_id=run_id_a,
        idempotency_key=run_id_a,
        created_at=now_iso,
        updated_at=now_iso,
    )
    with open_app_state_db() as conn:
        run_repo.save(conn, record_a)

    # User B tries to read User A's run
    resp = client.get(f"/api/v1/public/agentic/runs/{run_id_a}", headers=headers_b)
    # User B must NOT see User A's run
    assert resp.status_code in (403, 404)


def test_idor_surface_memories_isolation(idor_fixture):
    from risk_dashboard.modules.agentic_core.application.memory_service import MemoryService

    client = idor_fixture["client"]
    acc_a = idor_fixture["acc_a"]
    headers_b = idor_fixture["headers_b"]

    # Seed User A memory
    mem_svc = MemoryService()
    mem_a = mem_svc.record_memory(
        account_id=acc_a.account_id,
        memory_type="preference",
        content="Alpha confidential secret preference",
        provenance="user_stated",
        consent_memory=True,
    )
    assert mem_a is not None

    # User B tries to delete User A's memory
    del_resp = client.delete(f"/api/me/agent-memory/{mem_a.memory_id}", headers=headers_b)
    assert del_resp.status_code in (403, 404)

    # User B lists memories -> should not include User A's memory
    list_resp = client.get("/api/me/agent-memory", headers=headers_b)
    assert list_resp.status_code == 200
    items = list_resp.json().get("items", [])
    assert all(item["memory_id"] != mem_a.memory_id for item in items)


def test_idor_surface_user_preferences_isolation(idor_fixture):
    from risk_dashboard.modules.auth.infrastructure.sqlite import SqliteAccountConsentRepository
    from risk_dashboard.modules.auth.schemas.principal import ConsentSnapshot

    client = idor_fixture["client"]
    acc_a = idor_fixture["acc_a"]
    headers_b = idor_fixture["headers_b"]

    # User A consents memory=True
    consents = SqliteAccountConsentRepository()
    consents.save(
        account_id=acc_a.account_id,
        consent=ConsentSnapshot(memory=True, analytics=True, policy_version="1.0.0"),
    )

    # User B calls GET /api/me/agent-preferences -> gets User B's preferences, not User A's
    resp_b = client.get("/api/me/agent-preferences", headers=headers_b)
    assert resp_b.status_code == 200
    data_b = resp_b.json()
    assert data_b.get("memory") is False or data_b.get("memory_mode") == "off"


def test_idor_surface_market_portfolio_isolation(idor_fixture):
    client = idor_fixture["client"]
    headers_a = idor_fixture["headers_a"]
    headers_b = idor_fixture["headers_b"]

    # User A adds FPT to watchlist
    add_resp = client.post(
        "/api/v1/market-portfolio/watchlist",
        headers=headers_a,
        json={"symbol": "FPT", "label": "Tech Alpha"},
    )
    assert add_resp.status_code == 200

    # User B gets watchlist -> must be empty
    get_resp_b = client.get("/api/v1/market-portfolio/watchlist", headers=headers_b)
    assert get_resp_b.status_code == 200
    items_b = get_resp_b.json().get("items", [])
    assert len(items_b) == 0

    # User B tries to delete User A's watchlist item
    del_resp_b = client.delete("/api/v1/market-portfolio/watchlist/FPT", headers=headers_b)
    # Even if successful or 404, User A's watchlist must remain intact
    get_resp_a = client.get("/api/v1/market-portfolio/watchlist", headers=headers_a)
    items_a = get_resp_a.json().get("items", [])
    assert any(item["symbol"] == "FPT" for item in items_a)


def test_idor_surface_bctc_upload_and_memo_isolation(idor_fixture):
    client = idor_fixture["client"]
    headers_a = idor_fixture["headers_a"]
    headers_b = idor_fixture["headers_b"]

    # 1. User A uploads a BCTC file
    csv_content = b"metric,2023,2024\nRevenue,1000,1200\nNet_Income,200,250\n"
    up_resp = client.post(
        "/financials/upload",
        files={"file": ("bctc_a.csv", csv_content, "text/csv")},
        headers=headers_a,
    )
    assert up_resp.status_code == 200
    upload_id_a = up_resp.json()["upload_id"]

    # User B tries to analyze User A's upload -> must be 404 (non-disclosing, avoids oracle)
    b_analyze_resp = client.post(
        f"/financials/uploads/{upload_id_a}/analyze",
        headers=headers_b,
    )
    assert b_analyze_resp.status_code == 404, f"Expected 404, got {b_analyze_resp.status_code}"

    # 2. User A creates a BCTC memo
    memo_payload = {
        "subject": "Confidential Memo Alpha",
        "scope": "public",
        "report_refs": [
            {
                "report_id": "report:vnm",
                "revision_id": "rev_123",
                "period": "2024Q3",
                "source": "vndirect",
                "fetched_at": "2026-09-01T00:00:00Z",
            }
        ],
        "evidence_rows": [
            {
                "claim_ref": "revenue",
                "amount": {
                    "value": 1200.0,
                    "unit": "VND_bn",
                    "provenance": {
                        "report_id": "report:vnm",
                        "revision_id": "rev_123",
                        "period": "2024Q3",
                        "source": "vndirect",
                        "fetched_at": "2026-09-01T00:00:00Z",
                    },
                },
            }
        ],
    }
    memo_resp = client.post(
        "/api/v1/public/bctc/agent/memos",
        headers=headers_a,
        json=memo_payload,
    )
    assert memo_resp.status_code == 200, f"Expected 200, got {memo_resp.status_code}: {memo_resp.text}"
    memo_id_a = memo_resp.json()["memo_id"]

    # User B tries to read User A's memo -> must be 404
    b_get_memo = client.get(f"/api/v1/public/bctc/agent/memos/{memo_id_a}", headers=headers_b)
    assert b_get_memo.status_code == 404

    # User B tries to delete User A's memo -> must be 404
    b_del_memo = client.delete(f"/api/v1/public/bctc/agent/memos/{memo_id_a}", headers=headers_b)
    assert b_del_memo.status_code == 404

    # User B lists memos -> must not see User A's memo
    b_list_memos = client.get("/api/v1/public/bctc/agent/memos", headers=headers_b)
    assert b_list_memos.status_code == 200
    b_memos = b_list_memos.json().get("items", [])
    assert all(m["memo_id"] != memo_id_a for m in b_memos)

    # 3. User A creates an agent run
    run_resp = client.post(
        "/api/v1/public/bctc/agent/runs",
        headers=headers_a,
        json={"skill_id": "bctc.explain_line_item.v1", "ticker": "FPT"},
    )
    assert run_resp.status_code == 200, f"Expected 200, got {run_resp.status_code}: {run_resp.text}"
    run_id_a = run_resp.json()["run_id"]

    # User B tries to read User A's run -> must be 404
    b_get_run = client.get(f"/api/v1/public/bctc/agent/runs/{run_id_a}", headers=headers_b)
    assert b_get_run.status_code == 404

