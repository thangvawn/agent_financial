from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from risk_dashboard.modules.agentic_core.application.graph import run_graph
from risk_dashboard.modules.agentic_core.application.run_service import RunService
from risk_dashboard.modules.agentic_core.domain.tools import RiskClass, ToolGrant, ToolManifest
from risk_dashboard.modules.agentic_core.schemas.envelope import (
    ExecutionBudget,
    TrustedExecutionEnvelope,
)
from risk_dashboard.modules.agentic_core.schemas.requests import AgentRunRequestV1
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal, ConsentSnapshot
from risk_dashboard.platform.ai_runtime.contracts import ModelMessage, ModelResult, ModelTask
from risk_dashboard.platform.ai_runtime.testing.fake_provider import FakeProvider
from risk_dashboard.platform.database import clear_db_path_cache, open_app_state_db
from risk_dashboard.platform.database.migrate import apply_migrations


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    db_path = tmp_path / "agent_improvements.db"
    monkeypatch.setenv("RISK_DASHBOARD_APP_STATE_DB", str(db_path))
    clear_db_path_cache()
    with open_app_state_db(db_path) as conn:
        apply_migrations(conn)
    yield db_path
    clear_db_path_cache()


class FakeReadTool:
    manifest = ToolManifest(
        tool_id="quant-read",
        name="Quant read",
        module="quant",
        risk_class=RiskClass.READ,
        version="1.0.0",
        description="Read fixture",
        required_capabilities=("quant:read",),
    )

    def __init__(self) -> None:
        self.last_grant = None

    async def execute(self, grant: ToolGrant) -> dict[str, str]:
        self.last_grant = grant
        return {"source": "fixture", "value": "42"}


def _envelope() -> TrustedExecutionEnvelope:
    return TrustedExecutionEnvelope(
        run_id="run-improvement",
        correlation_id="correlation-improvement",
        idempotency_key="idempotency-improvement",
        account_id="account-improvement",
        surface="pro_lab",
        requested_operation="inspect",
        requested_resource_id="ticker:VCB:revenue",
        allowed_capabilities=("quant:read",),
        budget=ExecutionBudget(),
        policy_version="v1",
        model_policy_version="v1",
        consent=ConsentSnapshot(policy_version="v1"),
        created_at="2026-09-26T00:00:00+00:00",
    )


def _task() -> ModelTask:
    return ModelTask(
        task_type="agentic_read",
        system_instructions_ref="agentic.v1",
        messages=(ModelMessage(role="user", content="read fixture"),),
        correlation_id="correlation-improvement",
    )


def _tool() -> FakeReadTool:
    return FakeReadTool()


class CapturingProvider(FakeProvider):
    def __init__(self) -> None:
        super().__init__()
        self.last_task = None

    async def generate(self, task):  # type: ignore[no-untyped-def]
        self.last_task = task
        return ModelResult(
            text="Reviewed fixture",
            parsed={"answer": "Reviewed fixture"},
            provider="fake",
            model="fake-model",
            latency_ms=0,
            finish_reason="stop",
        )


def test_reviewer_receives_escaped_verified_tool_evidence() -> None:
    provider = CapturingProvider()
    tool = _tool()
    result = asyncio.run(run_graph(_envelope(), _task(), provider, tool))

    assert result["status"] == "success"
    assert provider.last_task is not None
    evidence_message = provider.last_task.messages[-1].content
    assert "VERIFIED TOOL EVIDENCE" in evidence_message
    assert '"value": "42"' in evidence_message
    assert "<verified_tool_evidence>" in evidence_message
    assert tool.last_grant is not None
    assert tool.last_grant.operation == "inspect"
    assert tool.last_grant.resource_id == "ticker:VCB:revenue"


def test_public_domain_scope_is_translated_to_manifest_capability() -> None:
    service = RunService()
    principal = AuthPrincipal(
        account_id="scope-account",
        session_id="scope-session",
        scopes=("learning:read",),
        resolved_at="2026-09-26T00:00:00+00:00",
    )
    envelope = service.build_envelope(
        AgentRunRequestV1(operation="learn.explain.v1", surface="learn_hub"),
        principal,
    )
    assert "learn:content:read" in envelope.allowed_capabilities


@pytest.mark.anyio
async def test_run_service_builds_context_and_deduplicates_idempotent_retries(test_db) -> None:
    service = RunService()
    principal = AuthPrincipal(
        account_id="agent-improvement-account",
        session_id="session-1",
        scopes=("agentic:run:execute", "learning:read"),
        resolved_at=datetime.now(timezone.utc).isoformat(),
    )
    request = AgentRunRequestV1(
        operation="analyze",
        surface="learn_hub",
        task_input={"question": "Tính tín hiệu cho VCB"},
        idempotency_key="agent-retry-001",
    )
    captured = []

    async def runner(envelope, task, provider, tool):  # type: ignore[no-untyped-def]
        captured.append((envelope, task))
        return {
            "status": "success",
            "text": "Đã phân tích",
            "evidence": {"value": "42"},
            "trace": ("guard", "router", "specialist", "reviewer", "success"),
            "tool_calls_used": 1,
            "tokens_used": 12,
            "cost_used": 0.001,
        }

    first = await service.create_and_execute_run(request=request, principal=principal, run_graph_fn=runner)
    second = await service.create_and_execute_run(request=request, principal=principal, run_graph_fn=runner)

    assert first.run_id == second.run_id
    assert len(captured) == 1
    assert '"question": "Tính tín hiệu cho VCB"' in captured[0][1].messages[2].content
    assert captured[0][0].idempotency_key == "agent-retry-001"
    assert first.artifact is not None
    assert first.artifact.content == "Đã phân tích"


@pytest.mark.anyio
async def test_run_trace_persists_redacted_task_input(test_db) -> None:
    service = RunService()
    principal = AuthPrincipal(
        account_id="redaction-account",
        session_id="session-redaction",
        scopes=("agentic:run:execute",),
        resolved_at="2026-09-26T00:00:00+00:00",
    )

    async def runner(envelope, task, provider, tool):  # type: ignore[no-untyped-def]
        return {"status": "success", "text": "ok", "trace": ("guard",)}

    response = await service.create_and_execute_run(
        request=AgentRunRequestV1(
            operation="analyze",
            surface="pro_lab",
            task_input={"email": "alice@example.com", "note": "safe"},
        ),
        principal=principal,
        run_graph_fn=runner,
    )
    trace = service.get_run_trace(run_id=response.run_id, account_id=principal.account_id)

    assert trace is not None
    assert "alice@example.com" not in str(trace["task_input"])
    assert "[REDACTED_PII]" in str(trace["task_input"])
