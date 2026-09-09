from __future__ import annotations

from datetime import datetime, timedelta, timezone
import pytest

from risk_dashboard.modules.agentic_core.application.tool_grants import resolve_grant, validate_grant
from risk_dashboard.modules.agentic_core.application.tool_registry import ToolRegistry, get_default_tool_registry
from risk_dashboard.modules.agentic_core.domain.tools import RiskClass, ToolGrant, ToolManifest
from risk_dashboard.modules.agentic_core.schemas.envelope import ExecutionBudget, TrustedExecutionEnvelope
from risk_dashboard.modules.auth.schemas.principal import ConsentSnapshot


def _envelope(capabilities: tuple[str, ...] = ("quant:read", "learning:read"), max_tool_calls: int = 16) -> TrustedExecutionEnvelope:
    return TrustedExecutionEnvelope(
        run_id="run-1",
        correlation_id="correlation-1",
        idempotency_key="idempotency-1",
        account_id="account-a",
        surface="pro_lab",
        allowed_capabilities=capabilities,
        budget=ExecutionBudget(max_tool_calls=max_tool_calls),
        policy_version="v1",
        model_policy_version="v1",
        consent=ConsentSnapshot(policy_version="v1"),
        created_at="2026-08-28T12:00:00+00:00",
    )


def test_forbidden_tool_suite_never_gets_grant() -> None:
    """AC2 Exit Gate: Forbidden tools MUST NEVER receive a grant under any circumstances."""
    registry = get_default_tool_registry()
    forbidden_tools = registry.list_tools(risk_class=RiskClass.FORBIDDEN)
    assert len(forbidden_tools) >= 5

    # Attacker tries with all capabilities allowed
    super_envelope = _envelope(capabilities=("*", "forbidden:trading", "forbidden:mutation", "forbidden:cms", "forbidden:trust"))

    for tool in forbidden_tools:
        grant = resolve_grant(super_envelope, tool)
        assert grant is None, f"Forbidden tool {tool.tool_id} MUST NOT receive grant!"


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

    # Missing capability
    no_cap_envelope = _envelope(capabilities=("other:read",))
    assert resolve_grant(no_cap_envelope, manifest) is None


def test_budget_exhaustion_blocks_grant() -> None:
    manifest = ToolManifest(
        tool_id="quant-read",
        name="Quant read",
        module="quant",
        risk_class=RiskClass.READ,
        version="1.0.0",
        description="Read only",
        required_capabilities=("quant:read",),
    )
    exhausted_envelope = _envelope(max_tool_calls=0)
    assert resolve_grant(exhausted_envelope, manifest) is None


def test_scoped_grant_validation() -> None:
    """AC2: validate_grant enforces one-run scope and expiration."""
    now_utc = datetime.now(timezone.utc)
    future_iso = (now_utc + timedelta(seconds=300)).isoformat()
    past_iso = (now_utc - timedelta(seconds=10)).isoformat()

    valid_grant = ToolGrant(
        grant_id="grant-1",
        run_id="run-1",
        tool_id="quant.explain_risk",
        expires_at=future_iso,
    )
    assert validate_grant(valid_grant, run_id="run-1", tool_id="quant.explain_risk") is True

    # Cross-run injection fails
    assert validate_grant(valid_grant, run_id="run-attacker", tool_id="quant.explain_risk") is False

    # Tool ID mismatch fails
    assert validate_grant(valid_grant, run_id="run-1", tool_id="other_tool") is False

    # Expired grant fails
    expired_grant = ToolGrant(
        grant_id="grant-expired",
        run_id="run-1",
        tool_id="quant.explain_risk",
        expires_at=past_iso,
    )
    assert validate_grant(expired_grant, run_id="run-1", tool_id="quant.explain_risk") is False


def test_tool_registry_versioning_and_lookup() -> None:
    registry = ToolRegistry()
    m1 = ToolManifest(
        tool_id="tool.a",
        name="Tool A v1",
        module="mod",
        risk_class=RiskClass.READ,
        version="1.0.0",
        description="desc",
    )
    m2 = ToolManifest(
        tool_id="tool.a",
        name="Tool A v2",
        module="mod",
        risk_class=RiskClass.READ,
        version="2.0.0",
        description="desc",
    )
    registry.register(m1)
    registry.register(m2)

    # Latest default lookup
    assert registry.get("tool.a") == m2
    assert registry.get("nonexistent") is None


def test_skill_manifest_loader_and_router() -> None:
    from risk_dashboard.modules.agentic_core.application.skill_router import SkillRouter
    from risk_dashboard.modules.agentic_core.infrastructure.domain_tools import (
        BctcResolveLineItemTool,
        LearningGetLessonContextTool,
    )
    from risk_dashboard.modules.agentic_core.infrastructure.quant_tool import QuantRiskReadOnlyTool
    from risk_dashboard.modules.agentic_core.infrastructure.skill_manifest_loader import SkillManifestLoader

    loader = SkillManifestLoader()
    manifests = loader.load_manifests()
    assert len(manifests) >= 8

    # Router maps surface/intent to domain tool
    bctc_tool = SkillRouter.resolve_tool("bctc_workspace", "bctc.resolve_line_item")
    assert isinstance(bctc_tool, BctcResolveLineItemTool)
    assert SkillRouter.get_required_capabilities(bctc_tool) == ("financials:read",)

    learn_tool = SkillRouter.resolve_tool("learn_hub", "get_lesson")
    assert isinstance(learn_tool, LearningGetLessonContextTool)
    assert SkillRouter.get_required_capabilities(learn_tool) == ("learning:read",)

    quant_tool = SkillRouter.resolve_tool("pro_lab", "explain_var")
    assert isinstance(quant_tool, QuantRiskReadOnlyTool)


def test_domain_tools_execute_with_valid_grants() -> None:
    import asyncio
    from risk_dashboard.modules.agentic_core.infrastructure.domain_tools import (
        BctcResolveLineItemTool,
        LearningGetLessonContextTool,
    )

    grant = ToolGrant(
        grant_id="g1",
        run_id="run-1",
        tool_id="bctc.resolve_line_item",
        expires_at="2099-01-01T00:00:00Z",
    )
    bctc_tool = BctcResolveLineItemTool()
    res_bctc = asyncio.run(bctc_tool.execute(grant))
    assert res_bctc["tool_id"] == "bctc.resolve_line_item"
    assert res_bctc["ticker"] == "FPT"
    assert res_bctc["value"] == "52618"

    learn_tool = LearningGetLessonContextTool()
    res_learn = asyncio.run(learn_tool.execute(grant))
    assert res_learn["tool_id"] == "learning.get_lesson_context"
    assert res_learn["lesson_id"] == "quant_101"

