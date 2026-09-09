from __future__ import annotations

from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import pytest

from risk_dashboard.api.main import app
from risk_dashboard.modules.auth.application.services import (
    RegisterAccount,
    ResolveSession,
    SessionInvalid,
)
from risk_dashboard.modules.auth.infrastructure.sqlite import (
    SqliteAccountConsentRepository,
    SqliteAccountRepository,
    SqliteAccountSessionRepository,
)
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal, ConsentSnapshot
from risk_dashboard.platform.database import clear_db_path_cache


@pytest.fixture
def auth_fixture(tmp_path, monkeypatch):
    db_path = str(tmp_path / "app_state.db")
    monkeypatch.setenv("RISK_DASHBOARD_APP_STATE_DB", db_path)
    clear_db_path_cache()
    accounts = SqliteAccountRepository()
    sessions = SqliteAccountSessionRepository()
    consents = SqliteAccountConsentRepository()

    account, session = RegisterAccount(accounts=accounts, sessions=sessions).execute(
        name="Test Remediation User",
        email=f"user-{tmp_path.name}@example.com",
        password="secure-password-123",
    )
    client = TestClient(app)
    return {
        "account": account,
        "session": session,
        "accounts": accounts,
        "sessions": sessions,
        "consents": consents,
        "client": client,
        "auth_headers": {"Authorization": f"Bearer {session.session_id}"},
    }


# ==============================================================================
# ID3: Consent Lifecycle Tests
# ==============================================================================

def test_run_service_honors_real_consent_and_blocks_memory_when_false(auth_fixture):
    from risk_dashboard.modules.agentic_core.application.run_service import RunService
    from risk_dashboard.modules.agentic_core.schemas.requests import AgentRunRequestV1
    from risk_dashboard.modules.agentic_core.application.memory_service import MemoryGovernor

    account = auth_fixture["account"]
    session = auth_fixture["session"]
    consents = auth_fixture["consents"]

    # Set real consent in DB: memory=False
    consents.save(
        account_id=account.account_id,
        consent=ConsentSnapshot(memory=False, analytics=False, policy_version="1.0.0"),
    )
    saved_consent = consents.get(account_id=account.account_id)

    principal = AuthPrincipal(
        account_id=account.account_id,
        session_id=session.session_id,
        assurance="session",
        scopes=("agentic:read",),
        consent=saved_consent,
        resolved_at=datetime.now(timezone.utc).isoformat(),
    )

    service = RunService()
    request = AgentRunRequestV1(
        surface="research",
        operation="fetch_market_signals",
        task_input={"symbol": "VCB"},
    )
    envelope = service.build_envelope(request, principal)

    # Must NOT be hardcoded memory=True
    assert envelope.consent is not None
    assert envelope.consent.memory is False
    assert envelope.consent.analytics is False

    # Governor must drop proposal when consent.memory is False
    proposal = MemoryGovernor.evaluate_proposal(
        account_id=principal.account_id,
        memory_type="preference",
        content="Prefers high tech stocks",
        provenance="user_stated",
        consent_memory=envelope.consent.memory,
    )
    assert proposal is None


# ==============================================================================
# ID4: User Rights & Privacy APIs (/api/me/*)
# ==============================================================================

def test_user_rights_preferences_get_and_patch(auth_fixture):
    client = auth_fixture["client"]
    headers = auth_fixture["auth_headers"]

    # 1. GET initial preferences
    resp = client.get("/api/me/agent-preferences", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "memory_mode" in data or "memory" in data

    # 2. PATCH preferences
    patch_resp = client.patch(
        "/api/me/agent-preferences",
        headers=headers,
        json={"memory": True, "analytics": True, "policy_version": "1.1.0"},
    )
    assert patch_resp.status_code == 200
    patch_data = patch_resp.json()
    assert patch_data.get("memory") is True or patch_data.get("memory_mode") == "on"


def test_user_rights_memory_crud_and_delete_all(auth_fixture):
    from risk_dashboard.modules.agentic_core.application.memory_service import MemoryService

    client = auth_fixture["client"]
    headers = auth_fixture["auth_headers"]
    account = auth_fixture["account"]

    # Seed 2 memory items
    mem_svc = MemoryService()
    mem1 = mem_svc.record_memory(
        account_id=account.account_id,
        memory_type="preference",
        content="Thích cổ phiếu công nghệ FPT",
        provenance="user_stated",
        consent_memory=True,
    )
    mem2 = mem_svc.record_memory(
        account_id=account.account_id,
        memory_type="goal",
        content="Quan tâm nhóm ngân hàng VCB",
        provenance="user_stated",
        consent_memory=True,
    )
    assert mem1 is not None and mem2 is not None

    # 1. GET memories
    get_resp = client.get("/api/me/agent-memory", headers=headers)
    assert get_resp.status_code == 200
    memories = get_resp.json().get("items", [])
    assert len(memories) >= 2

    # 2. DELETE single memory
    del_resp = client.delete(f"/api/me/agent-memory/{mem1.memory_id}", headers=headers)
    assert del_resp.status_code in (200, 204)

    # 3. DELETE all memories
    del_all_resp = client.delete("/api/me/agent-memory", headers=headers)
    assert del_all_resp.status_code in (200, 204)

    # Verify empty
    verify_resp = client.get("/api/me/agent-memory", headers=headers)
    assert verify_resp.status_code == 200
    assert len(verify_resp.json().get("items", [])) == 0


def test_user_rights_data_export(auth_fixture):
    client = auth_fixture["client"]
    headers = auth_fixture["auth_headers"]
    account = auth_fixture["account"]

    resp = client.post("/api/me/agent-data-export", headers=headers)
    assert resp.status_code == 200
    export_data = resp.json()
    assert export_data.get("account_id") == account.account_id
    assert "export_timestamp" in export_data or "exported_at" in export_data
    assert "data" in export_data or "memories" in export_data


# ==============================================================================
# ID1: Canonical Principal (Scopes động, Anonymous, Recent Auth)
# ==============================================================================

def test_scope_resolver_tier_mapping():
    from risk_dashboard.modules.auth.application.scope_resolver import resolve_scopes

    free_scopes = resolve_scopes(tier="community", role="user")
    assert "account:market_portfolio:read" in free_scopes
    assert "pro:pro_lab:use" not in free_scopes

    pro_scopes = resolve_scopes(tier="pro", role="user")
    assert "pro:pro_lab:use" in pro_scopes

    admin_scopes = resolve_scopes(tier="enterprise", role="admin")
    assert "admin:pro_lab:manage" in admin_scopes


def test_anonymous_principal_has_ephemeral_namespace_and_no_memory():
    from risk_dashboard.modules.auth.application.dependencies import resolve_principal_relaxed

    # Relaxed dependency for public endpoints without bearer token
    principal = resolve_principal_relaxed(authorization=None)
    assert principal.is_anonymous is True
    assert principal.account_id.startswith("anon_")
    assert principal.assurance == "anonymous"
    assert principal.consent is None or principal.consent.memory is False


def test_recent_auth_assurance_resolution(auth_fixture):
    from risk_dashboard.modules.auth.application.dependencies import resolve_principal

    session = auth_fixture["session"]
    # Session just created -> should be recent_auth
    principal = resolve_principal(authorization=f"Bearer {session.session_id}")
    assert principal.assurance in ("recent_auth", "session")


# ==============================================================================
# ID5: Session Hardening (Session Rotation)
# ==============================================================================

def test_session_rotation(auth_fixture):
    client = auth_fixture["client"]
    session = auth_fixture["session"]
    sessions = auth_fixture["sessions"]
    headers = auth_fixture["auth_headers"]

    # Rotate session
    resp = client.post("/api/v1/public/auth/rotate-session", headers=headers)
    assert resp.status_code == 200
    new_session_id = resp.json().get("session_id")
    assert new_session_id is not None
    assert new_session_id != session.session_id

    # Old session must be revoked
    old_session_obj = sessions.get(session_id=session.session_id)
    assert old_session_obj.status == "revoked"

    # New session must be valid
    resolve_svc = ResolveSession(accounts=auth_fixture["accounts"], sessions=sessions)
    acc, new_s = resolve_svc.execute(session_id=new_session_id)
    assert acc.account_id == auth_fixture["account"].account_id
    assert new_s.status == "active"


# ==============================================================================
# ID6 & ID7: Audit Drill, Log PII Redaction, Retention TTL
# ==============================================================================

def test_audit_service_break_glass_event(auth_fixture):
    from risk_dashboard.modules.auth.application.audit_service import AuditLogService

    audit_svc = AuditLogService()
    event = audit_svc.log_event(
        event_type="break_glass_access",
        actor_id="admin_001",
        target_account_id=auth_fixture["account"].account_id,
        reason="Security Incident Investigation INC-992",
    )
    assert event.event_id.startswith("audit_")

    records = audit_svc.query_events(event_type="break_glass_access")
    assert any(r.event_id == event.event_id for r in records)


def test_pii_log_redaction_filter():
    from risk_dashboard.platform.logging.pii_filter import redact_pii

    raw = "User email user@financial.vn with key sk-live-992837482910 and phone 0912345678"
    redacted = redact_pii(raw)
    assert "user@financial.vn" not in redacted
    assert "sk-live-992837482910" not in redacted
    assert "[REDACTED" in redacted


def test_retention_ttl_service(auth_fixture):
    from risk_dashboard.modules.auth.application.retention_service import RetentionService

    sessions = auth_fixture["sessions"]
    account = auth_fixture["account"]

    # Create expired session in past
    from risk_dashboard.modules.auth.application.security import AccountSession
    expired_sess = AccountSession(
        session_id="expired_sess_123456",
        account_id=account.account_id,
        status="active",
        created_at="2020-01-01T00:00:00+00:00",
        last_seen_at="2020-01-01T00:00:00+00:00",
        expires_at="2020-01-15T00:00:00+00:00",
    )
    sessions.save(expired_sess)

    retention_svc = RetentionService(sessions=sessions)
    purged_count = retention_svc.purge_expired_sessions()
    assert purged_count >= 1

    reloaded = sessions.get(session_id="expired_sess_123456")
    assert reloaded is None or reloaded.status == "revoked"
