from __future__ import annotations

from risk_dashboard.modules.agentic_core.application.tool_grants import resolve_grant
from risk_dashboard.modules.agentic_core.domain.tools import RiskClass, ToolManifest
from risk_dashboard.modules.agentic_core.schemas.envelope import TrustedExecutionEnvelope
from risk_dashboard.modules.auth.schemas.principal import ConsentSnapshot


def _envelope() -> TrustedExecutionEnvelope:
    return TrustedExecutionEnvelope(
        run_id="run-1",
        correlation_id="correlation-1",
        idempotency_key="idempotency-1",
        account_id="account-a",
        surface="pro_lab",
        allowed_capabilities=("quant:read",),
        policy_version="v1",
        model_policy_version="v1",
        consent=ConsentSnapshot(policy_version="v1"),
        created_at="2026-08-28T12:00:00+00:00",
    )


def test_forbidden_tool_never_gets_grant() -> None:
    manifest = ToolManifest(
        tool_id="blocked",
        name="Blocked",
        module="agentic_core",
        risk_class=RiskClass.FORBIDDEN,
        version="1.0.0",
        description="Blocked",
    )
    assert resolve_grant(_envelope(), manifest) is None


def test_confirmed_write_requires_confirmation_flow() -> None:
    manifest = ToolManifest(
        tool_id="write",
        name="Write",
        module="agentic_core",
        risk_class=RiskClass.CONFIRMED_WRITE,
        version="1.0.0",
        description="Must be confirmed",
    )
    assert resolve_grant(_envelope(), manifest) is None


def test_grant_requires_capability_and_scopes_to_run() -> None:
    manifest = ToolManifest(
        tool_id="quant-read",
        name="Quant read",
        module="quant",
        risk_class=RiskClass.READ,
        version="1.0.0",
        description="Read only",
        required_capabilities=("quant:read",),
    )
    grant = resolve_grant(_envelope(), manifest)
    assert grant is not None
    assert grant.run_id == "run-1"
    assert grant.tool_id == "quant-read"
