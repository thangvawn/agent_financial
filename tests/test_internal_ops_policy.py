from __future__ import annotations

from datetime import datetime, timezone, timedelta
import pytest

from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.internal_ops.application.policy import (
    GrantExpiredError,
    InvalidPurposeError,
    OpsRole,
    PolicyDeniedError,
    PolicyEngine,
    PurposeGrant,
)
from risk_dashboard.modules.internal_ops.domain.contracts import FORBIDDEN_TOOL_NAMES


def _make_principal(scopes: tuple[str, ...] = ()) -> AuthPrincipal:
    return AuthPrincipal(
        account_id="admin-001",
        session_id="sess-001",
        scopes=scopes,
        resolved_at="2026-09-05T10:00:00Z",
    )


def test_resolve_role_from_scopes():
    p_admin = _make_principal(("admin:internal_ops:security_admin",))
    assert PolicyEngine.resolve_role(p_admin) == OpsRole.SECURITY_ADMIN

    p_trust = _make_principal(("admin:internal_ops:trust_reviewer",))
    assert PolicyEngine.resolve_role(p_trust) == OpsRole.TRUST_REVIEWER

    p_cms = _make_principal(("admin:internal_ops:content_operator",))
    assert PolicyEngine.resolve_role(p_cms) == OpsRole.CONTENT_OPERATOR

    p_rel = _make_principal(("admin:internal_ops:reliability_operator",))
    assert PolicyEngine.resolve_role(p_rel) == OpsRole.RELIABILITY_OPERATOR

    p_viewer = _make_principal(("admin:internal_ops:support_viewer",))
    assert PolicyEngine.resolve_role(p_viewer) == OpsRole.SUPPORT_VIEWER


def test_missing_scopes_denied():
    p_unauth = _make_principal(())
    with pytest.raises(PolicyDeniedError):
        PolicyEngine.resolve_role(p_unauth)


def test_purpose_validation():
    p = _make_principal(("admin:internal_ops:support_viewer",))
    with pytest.raises(InvalidPurposeError):
        PolicyEngine.create_grant(p, purpose="short")

    grant = PolicyEngine.create_grant(p, purpose="Valid investigation purpose")
    assert grant.purpose == "Valid investigation purpose"
    assert grant.role == OpsRole.SUPPORT_VIEWER
    assert "analytics_monitoring" in grant.allowed_modules


def test_module_access_matrix():
    p_viewer = _make_principal(("admin:internal_ops:support_viewer",))
    grant_viewer = PolicyEngine.create_grant(p_viewer, purpose="Check KPI metrics")
    assert grant_viewer.allowed_modules == ("analytics_monitoring",)

    # Viewer requesting trust_safety is denied
    with pytest.raises(PolicyDeniedError):
        PolicyEngine.create_grant(
            p_viewer,
            purpose="Investigate incident",
            requested_modules=("trust_safety",),
        )

    # Content operator can access cms
    p_cms = _make_principal(("admin:internal_ops:content_operator",))
    grant_cms = PolicyEngine.create_grant(p_cms, purpose="Review content quality")
    assert "admin_cms" in grant_cms.allowed_modules
    assert "analytics_monitoring" in grant_cms.allowed_modules


def test_expired_grant_rejected():
    past_iso = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
    grant = PurposeGrant(
        grant_id="grant-old",
        account_id="admin-001",
        role=OpsRole.SUPPORT_VIEWER,
        purpose="Old purpose test",
        allowed_modules=("analytics_monitoring",),
        expires_at=past_iso,
    )
    assert not PolicyEngine.is_grant_valid(grant)
    with pytest.raises(GrantExpiredError):
        PolicyEngine.authorize_tool_call(grant, "ops.get_kpi_slice@1.0.0", "analytics_monitoring")


def test_forbidden_tools_cannot_be_authorized():
    p_sec = _make_principal(("admin:internal_ops:security_admin",))
    grant = PolicyEngine.create_grant(p_sec, purpose="Security incident triage")
    for forbidden in FORBIDDEN_TOOL_NAMES:
        with pytest.raises(PolicyDeniedError) as excinfo:
            PolicyEngine.authorize_tool_call(grant, forbidden)
        assert "forbidden" in str(excinfo.value)


def test_breakglass_rules():
    p_sec = _make_principal(("admin:internal_ops:security_admin",))
    # Breakglass requires reason >= 8 chars
    with pytest.raises(InvalidPurposeError):
        PolicyEngine.create_grant(
            p_sec,
            purpose="Emergency triage",
            breakglass=True,
            breakglass_reason="short",
        )

    # Breakglass TTL capped at 900s (15 min)
    grant = PolicyEngine.create_grant(
        p_sec,
        purpose="Emergency incident response",
        ttl_seconds=3600,
        breakglass=True,
        breakglass_reason="Severity 1 data pipeline outage",
    )
    assert grant.is_breakglass is True
    exp = datetime.fromisoformat(grant.expires_at)
    diff = (exp - datetime.now(timezone.utc)).total_seconds()
    assert diff <= 905  # Within 15 min + tolerance

    # Non-security admin cannot breakglass
    p_viewer = _make_principal(("admin:internal_ops:support_viewer",))
    with pytest.raises(PolicyDeniedError):
        PolicyEngine.create_grant(
            p_viewer,
            purpose="Emergency viewer",
            breakglass=True,
            breakglass_reason="Trying breakglass",
        )

