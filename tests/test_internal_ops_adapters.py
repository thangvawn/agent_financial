from __future__ import annotations

import inspect
from unittest.mock import MagicMock
import pytest

from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.internal_ops.application.policy import (
    OpsRole,
    PolicyEngine,
    PurposeGrant,
)
from risk_dashboard.modules.internal_ops.application.redaction import RedactionEngine
from risk_dashboard.modules.internal_ops.infrastructure.adapters.admin_cms import AdminCmsAdapter
from risk_dashboard.modules.internal_ops.infrastructure.adapters.agentic_core import AgenticCoreAdapter
from risk_dashboard.modules.internal_ops.infrastructure.adapters.analytics import AnalyticsAdapter
from risk_dashboard.modules.internal_ops.infrastructure.adapters.trust_safety import TrustSafetyAdapter


def _grant(role: OpsRole, purpose: str, allowed: tuple[str, ...]) -> PurposeGrant:
    return PurposeGrant(
        grant_id="grant-test-123",
        account_id="admin-001",
        role=role,
        purpose=purpose,
        allowed_modules=allowed,
        expires_at="2099-01-01T00:00:00Z",
    )


def test_redaction_secrets_and_pii():
    text = "User test@example.com with phone 0912345678 and key sk-abcdef1234567890abcdef123 leaked canary_secret_super_secret"
    clean, tags = RedactionEngine.redact_text(text)
    assert "test@example.com" not in clean
    assert "0912345678" not in clean
    assert "sk-abcdef" not in clean
    assert "canary_secret" not in clean
    assert "[REDACTED_EMAIL]" in clean
    assert "[REDACTED_PHONE]" in clean
    assert "[REDACTED_API_KEY]" in clean
    assert "[REDACTED_CANARY]" in clean
    assert len(tags) >= 3


def test_redaction_filter_dict_allowlist():
    raw_dict = {
        "kpi_name": "latency",
        "metric_value": 150,
        "internal_secret_token": "secret_token_val",
        "extra_unknown_field": "discard_me",
    }
    filtered, tags = RedactionEngine.filter_and_redact_dict(raw_dict, allowlist={"kpi_name", "metric_value"})
    assert "kpi_name" in filtered
    assert "metric_value" in filtered
    assert "internal_secret_token" not in filtered
    assert "extra_unknown_field" not in filtered


def test_analytics_adapter_calls_service():
    mock_kpi_svc = MagicMock()
    mock_item = MagicMock()
    mock_item.model_dump.return_value = {
        "kpi_name": "cache_hit_ratio",
        "metric_value": 0.94,
        "as_of": "2026-09-05T10:00:00Z",
        "leaked_canary": "canary_secret_in_kpi",
    }
    mock_kpi_svc.execute.return_value = [mock_item]

    adapter = AnalyticsAdapter(list_kpi_service=mock_kpi_svc)
    grant = _grant(OpsRole.SUPPORT_VIEWER, "Investigate KPI ratios", ("analytics_monitoring",))
    batch = adapter.get_kpi_slice(grant, kpi_name="cache_hit_ratio")

    assert batch.status == "available"
    assert len(batch.items) == 1
    item = batch.items[0]
    assert item.ref.source_module == "analytics_monitoring"
    assert item.ref.resource_id == "cache_hit_ratio"
    assert "leaked_canary" not in item.fields
    mock_kpi_svc.execute.assert_called_once_with(kpi_name="cache_hit_ratio", window_grain=None)


def test_trust_safety_adapter_canary_and_purpose():
    mock_incidents_svc = MagicMock()
    mock_inc = MagicMock()
    mock_inc.model_dump.return_value = {
        "incident_id": "inc-999",
        "surface": "learn",
        "severity": "high",
        "title": "Contact admin at security@example.com for canary_secret_token_123",
        "summary": "Sample summary",
        "internal_db_row": "strip_me",
    }
    mock_incidents_svc.execute.return_value = [mock_inc]
    mock_audit_svc = MagicMock()
    mock_audit_svc.execute.return_value = []

    adapter = TrustSafetyAdapter(audit_service=mock_audit_svc, incidents_service=mock_incidents_svc)
    grant = _grant(OpsRole.TRUST_REVIEWER, "Safety review incident investigation", ("trust_safety",))
    batch = adapter.get_trust_case(grant, surface="learn")

    assert batch.status == "available"
    assert len(batch.items) == 1
    item = batch.items[0]
    assert "security@example.com" not in item.fields["title"]
    assert "canary_secret" not in item.fields["title"]
    assert "internal_db_row" not in item.fields


def test_admin_cms_adapter_calls_read_only():
    mock_content_svc = MagicMock()
    mock_item = MagicMock()
    mock_item.model_dump.return_value = {
        "content_id": "lesson-101",
        "title": "Quantum VaR Basics",
        "status": "published",
        "updated_at": "2026-09-05T08:00:00Z",
    }
    mock_content_svc.execute.return_value = [mock_item]

    adapter = AdminCmsAdapter(list_content_svc=mock_content_svc)
    grant = _grant(OpsRole.CONTENT_OPERATOR, "QA published lesson content", ("admin_cms",))
    batch = adapter.get_content_context(grant)

    assert batch.status == "available"
    assert len(batch.items) == 1
    assert batch.items[0].ref.resource_id == "lesson-101"


def test_agentic_core_adapter_disabled():
    adapter = AgenticCoreAdapter()
    grant = _grant(OpsRole.RELIABILITY_OPERATOR, "Inspect run failure", ("agentic_core",))
    batch = adapter.get_run_trace(grant, "run-123")
    assert batch.status == "source_unavailable"
    assert len(batch.items) == 0


def test_adapters_have_no_http_or_shell():
    adapters = [AnalyticsAdapter, TrustSafetyAdapter, AdminCmsAdapter, AgenticCoreAdapter]
    for cls in adapters:
        src = inspect.getsource(cls)
        assert "requests." not in src
        assert "httpx." not in src
        assert "subprocess" not in src
        assert "os.system" not in src

