"""Tests for quant_research tool manifests and grants (QF1 Exit Gate)."""
from __future__ import annotations

from risk_dashboard.modules.agentic_core.application.tool_grants import resolve_grant
from risk_dashboard.modules.agentic_core.domain.tools import RiskClass, ToolManifest
from risk_dashboard.modules.agentic_core.schemas.envelope import TrustedExecutionEnvelope
from risk_dashboard.modules.auth.schemas.principal import ConsentSnapshot
from risk_dashboard.modules.quant_research.tools.manifests import (
    ALL_QUANT_TOOL_MANIFESTS,
    QUANT_EOD_MANIFEST,
    QUANT_MODEL_REPORT_MANIFEST,
    QUANT_SCENARIO_MANIFEST,
)


def _make_envelope(capabilities: tuple[str, ...]) -> TrustedExecutionEnvelope:
    return TrustedExecutionEnvelope(
        run_id="run-quant-test",
        correlation_id="corr-quant-test",
        idempotency_key="idemp-quant-test",
        account_id="acc-quant-user",
        surface="quant_research",
        allowed_capabilities=capabilities,
        policy_version="1.0.0",
        model_policy_version="1.0.0",
        consent=ConsentSnapshot(policy_version="1.0.0"),
        created_at="2026-09-05T12:00:00+00:00",
    )


def test_manifest_metadata_and_risk_classes() -> None:
    assert len(ALL_QUANT_TOOL_MANIFESTS) == 3
    for manifest in ALL_QUANT_TOOL_MANIFESTS:
        assert manifest.module == "quant_research"
        assert manifest.risk_class == RiskClass.READ
        assert manifest.version == "1.0.0"
        assert len(manifest.required_capabilities) == 1
        assert manifest.tool_id in {
            "quant.eod_analysis.v1",
            "quant.scenario_compare.v1",
            "quant.model_report.v1",
        }


def test_grant_authorized_with_required_capabilities() -> None:
    env = _make_envelope((
        "quant_research:analysis:read",
        "quant_research:scenario:read",
        "quant_research:model_report:read",
    ))

    g_eod = resolve_grant(env, QUANT_EOD_MANIFEST)
    assert g_eod is not None
    assert g_eod.tool_id == "quant.eod_analysis.v1"
    assert g_eod.run_id == "run-quant-test"

    g_scen = resolve_grant(env, QUANT_SCENARIO_MANIFEST)
    assert g_scen is not None
    assert g_scen.tool_id == "quant.scenario_compare.v1"

    g_model = resolve_grant(env, QUANT_MODEL_REPORT_MANIFEST)
    assert g_model is not None
    assert g_model.tool_id == "quant.model_report.v1"


def test_grant_denied_when_missing_capability() -> None:
    # Envelope only has scenario capability, not analysis capability
    env = _make_envelope(("quant_research:scenario:read",))

    g_eod = resolve_grant(env, QUANT_EOD_MANIFEST)
    assert g_eod is None, "EOD grant must be denied when missing quant_research:analysis:read"

    g_scen = resolve_grant(env, QUANT_SCENARIO_MANIFEST)
    assert g_scen is not None


def test_forbidden_and_mutation_tools_never_granted() -> None:
    env = _make_envelope(("quant_research:write",))

    forbidden_tool = ToolManifest(
        tool_id="quant.arbitrary_eval.v1",
        name="Arbitrary code execution",
        module="quant_research",
        risk_class=RiskClass.FORBIDDEN,
        version="1.0.0",
        description="Forbidden",
        required_capabilities=("quant_research:write",),
    )
    assert resolve_grant(env, forbidden_tool) is None

    mutation_tool = ToolManifest(
        tool_id="quant.mutate_order.v1",
        name="Order placement",
        module="quant_research",
        risk_class=RiskClass.CONFIRMED_WRITE,
        version="1.0.0",
        description="Confirmed write",
        required_capabilities=("quant_research:write",),
    )
    assert resolve_grant(env, mutation_tool) is None

