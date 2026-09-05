from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
import pytest

from risk_dashboard.modules.internal_ops.application.policy import (
    GrantExpiredError,
    OpsRole,
    PolicyDeniedError,
    PurposeGrant,
)
from risk_dashboard.modules.internal_ops.domain.contracts import (
    EvidenceBatch,
    EvidenceRef,
    FORBIDDEN_TOOL_NAMES,
)
from risk_dashboard.modules.internal_ops.domain.tools import (
    ALLOWED_TOOL_MANIFESTS,
    InvestigationToolGrant,
    ToolManifest,
    ToolRegistry,
)


def _purpose_grant() -> PurposeGrant:
    return PurposeGrant(
        grant_id="grant-1",
        account_id="admin-001",
        role=OpsRole.SECURITY_ADMIN,
        purpose="Comprehensive investigation",
        allowed_modules=("analytics_monitoring", "trust_safety", "admin_cms", "agentic_core"),
        expires_at="2099-01-01T00:00:00Z",
    )


def _tool_grant(tool_id: str, max_calls: int = 5, expires_at: str | None = None) -> InvestigationToolGrant:
    exp = expires_at or (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    return InvestigationToolGrant(
        grant_id="tgrant-1",
        investigation_id="inv-100",
        tool_id=tool_id,
        purpose="Investigate ops anomaly",
        expires_at=exp,
        max_calls=max_calls,
    )


def test_allowed_manifests_count_and_properties():
    assert len(ALLOWED_TOOL_MANIFESTS) == 9
    for tool_id, manifest in ALLOWED_TOOL_MANIFESTS.items():
        assert manifest.version == "1.0.0"
        assert manifest.tool_id == tool_id
        assert manifest.risk_class in ("read", "proposal")
        # Roundtrip
        dumped = manifest.model_dump()
        reconstructed = ToolManifest.model_validate(dumped)
        assert reconstructed == manifest


def test_forbidden_tools_not_registered():
    for f_tool in FORBIDDEN_TOOL_NAMES:
        assert f_tool not in ALLOWED_TOOL_MANIFESTS
        with pytest.raises(PolicyDeniedError):
            ToolRegistry.get_manifest(f_tool)


def test_tool_grant_call_limit():
    tg = _tool_grant("ops.get_kpi_slice@1.0.0", max_calls=2)
    tg.consume()
    assert tg.call_count == 1
    tg.consume()
    assert tg.call_count == 2
    with pytest.raises(PolicyDeniedError) as excinfo:
        tg.consume()
    assert "exhausted" in str(excinfo.value)


def test_tool_grant_expired():
    past_iso = (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()
    tg = _tool_grant("ops.get_kpi_slice@1.0.0", expires_at=past_iso)
    with pytest.raises(GrantExpiredError):
        tg.consume()


def test_disabled_tools_return_source_unavailable():
    tg = _tool_grant("ops.get_run_trace@1.0.0")
    pg = _purpose_grant()
    res = ToolRegistry.execute("ops.get_run_trace@1.0.0", tg, pg, {}, {})
    assert isinstance(res, EvidenceBatch)
    assert res.status == "source_unavailable"


def test_propose_content_fix_tool():
    tg = _tool_grant("ops.propose_content_fix@1.0.0")
    pg = _purpose_grant()
    ref = EvidenceRef(
        source_module="admin_cms",
        resource_type="cms_content",
        resource_id="lesson-404",
        observed_at="2026-09-05T10:00:00Z",
    )
    rec = ToolRegistry.execute(
        "ops.propose_content_fix@1.0.0",
        tg,
        pg,
        {},
        {"target_ref": ref, "rationale": "Fix formula explanation typo"},
    )
    assert rec.executable is False
    assert rec.status == "draft"
    assert rec.action_kind == "content_draft_fix"
    assert rec.target_ref.resource_id == "lesson-404"


def test_tool_execution_dispatches_to_analytics_adapter():
    mock_analytics = MagicMock()
    mock_analytics.get_kpi_slice.return_value = EvidenceBatch(
        items=(),
        source_module="analytics_monitoring",
        fetched_at="2026-09-05T10:00:00Z",
        status="available",
    )
    adapters = {"analytics": mock_analytics}
    tg = _tool_grant("ops.get_kpi_slice@1.0.0")
    pg = _purpose_grant()
    res = ToolRegistry.execute(
        "ops.get_kpi_slice@1.0.0",
        tg,
        pg,
        adapters,
        {"kpi_name": "api_health"},
    )
    assert res.status == "available"
    mock_analytics.get_kpi_slice.assert_called_once()

