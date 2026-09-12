from __future__ import annotations

import asyncio

import pytest

from risk_dashboard.modules.agentic_core.application import graph as graph_module
from risk_dashboard.modules.agentic_core.application.graph import run_graph
from risk_dashboard.modules.agentic_core.domain.tools import RiskClass, ToolGrant, ToolManifest
from risk_dashboard.modules.agentic_core.infrastructure.quant_tool import QuantRiskReadOnlyTool
from risk_dashboard.modules.agentic_core.schemas.claim import Claim, ClaimKind, ClaimStatus
from risk_dashboard.modules.agentic_core.schemas.envelope import ExecutionBudget, TrustedExecutionEnvelope
from risk_dashboard.modules.auth.schemas.principal import ConsentSnapshot
from risk_dashboard.platform.ai_runtime.contracts import ModelError, ModelMessage, ModelResult, ModelTask
from risk_dashboard.platform.ai_runtime.testing.fake_provider import FakeProvider


class FakeReadTool:
    def __init__(
        self,
        manifest: ToolManifest,
        *,
        delay_seconds: float = 0,
        started: asyncio.Event | None = None,
    ) -> None:
        self.manifest = manifest
        self.calls = 0
        self.delay_seconds = delay_seconds
        self.started = started

    async def execute(self, grant: ToolGrant) -> dict[str, str]:
        self.calls += 1
        if self.started:
            self.started.set()
        if self.delay_seconds:
            await asyncio.sleep(self.delay_seconds)
        return {"source": "fixture", "value": "42"}


def _envelope(**budget: int) -> TrustedExecutionEnvelope:
    return TrustedExecutionEnvelope(
        run_id="run-1",
        correlation_id="correlation-1",
        idempotency_key="idempotency-1",
        account_id="account-a",
        surface="pro_lab",
        allowed_capabilities=("quant:read",),
        budget=ExecutionBudget(**budget),
        policy_version="v1",
        model_policy_version="v1",
        consent=ConsentSnapshot(policy_version="v1"),
        created_at="2026-08-28T12:00:00+00:00",
    )


def _task(task_type: str = "agentic_read") -> ModelTask:
    return ModelTask(
        task_type=task_type,
        system_instructions_ref="agentic.v1",
        messages=(ModelMessage(role="user", content="read fixture"),),
        correlation_id="correlation-1",
    )


def _tool(
    risk_class: RiskClass = RiskClass.READ,
    *,
    delay_seconds: float = 0,
    started: asyncio.Event | None = None,
) -> FakeReadTool:
    return FakeReadTool(
        ToolManifest(
            tool_id="quant-read",
            name="Quant read",
            module="quant",
            risk_class=risk_class,
            version="1.0.0",
            description="Read fixture",
            required_capabilities=("quant:read",),
        ),
        delay_seconds=delay_seconds,
        started=started,
    )


def _result() -> ModelResult:
    return ModelResult(
        text="Reviewed fixture",
        parsed={"answer": "42"},
        provider="fake",
        model="fake-model",
        latency_ms=0,
        finish_reason="stop",
    )


def test_graph_runs_offline_with_fake_provider_and_read_tool() -> None:
    tool = _tool()
    result = asyncio.run(run_graph(_envelope(), _task(), FakeProvider([_result()]), tool))

    assert result["status"] == "success"
    assert result["code"] is None
    assert result["text"] == "Reviewed fixture"
    assert result["evidence"] == {"source": "fixture", "value": "42"}
    assert result["trace"] == ("guard", "router", "specialist", "reviewer", "success")
    assert result["steps_used"] == 5
    assert result["tool_calls_used"] == 1
    assert "tokens_used" in result and result["tokens_used"] > 0
    assert "cost_used" in result and result["cost_used"] >= 0
    assert tool.calls == 1


def test_graph_rejects_forbidden_tool_before_provider_call() -> None:
    tool = _tool(RiskClass.FORBIDDEN)
    result = asyncio.run(run_graph(_envelope(), _task(), FakeProvider([_result()]), tool))

    assert result["status"] == "recovery"
    assert result["code"] == "tool_not_granted"
    assert result["text"] is None
    assert tool.calls == 0


def test_graph_recovers_unknown_task_without_side_effect() -> None:
    tool = _tool()
    result = asyncio.run(run_graph(_envelope(), _task("unknown"), FakeProvider([_result()]), tool))

    assert result["status"] == "recovery"
    assert result["code"] == "unknown_task_type"
    assert result["trace"] == ("guard", "recovery")
    assert tool.calls == 0


def test_graph_recovers_provider_error() -> None:
    tool = _tool()
    provider = FakeProvider([ModelError("provider_unavailable", "Offline failure")])

    result = asyncio.run(run_graph(_envelope(), _task(), provider, tool))

    assert result["status"] == "recovery"
    assert result["code"] == "provider_unavailable"
    assert result["text"] is None
    assert tool.calls == 1


def test_graph_blocks_exhausted_tool_budget_before_side_effect() -> None:
    tool = _tool()
    result = asyncio.run(
        run_graph(_envelope(max_tool_calls=0), _task(), FakeProvider([_result()]), tool)
    )

    assert result["status"] == "recovery"
    assert result["code"] == "tool_budget_exhausted"
    assert result["trace"] == ("recovery",)
    assert tool.calls == 0


def test_graph_recovers_when_tool_exceeds_wall_budget() -> None:
    tool = _tool(delay_seconds=0.02)
    result = asyncio.run(
        run_graph(
            _envelope(max_wall_seconds=0.01),
            _task(),
            FakeProvider([_result()]),
            tool,
        )
    )

    assert result["status"] == "recovery"
    assert result["code"] == "wall_budget_exhausted"
    assert result["tool_calls_used"] == 1
    assert tool.calls == 1


def test_graph_does_not_start_tool_when_wall_budget_is_exhausted(monkeypatch) -> None:
    tool = _tool()
    monkeypatch.setattr(graph_module, "_remaining_wall_seconds", lambda state: 0)

    result = asyncio.run(run_graph(_envelope(), _task(), FakeProvider([_result()]), tool))

    assert result["status"] == "recovery"
    assert result["code"] == "wall_budget_exhausted"
    assert result["tool_calls_used"] == 0
    assert tool.calls == 0


def test_graph_propagates_cancellation_during_tool_execution() -> None:
    async def cancel_run() -> None:
        started = asyncio.Event()
        task = asyncio.create_task(
            run_graph(_envelope(), _task(), FakeProvider([_result()]), _tool(delay_seconds=1, started=started))
        )
        await started.wait()
        task.cancel()
        await task

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(cancel_run())


def test_graph_deterministic_replay() -> None:
    tool_1 = _tool()
    tool_2 = _tool()
    provider_1 = FakeProvider([_result()])
    provider_2 = FakeProvider([_result()])

    res_1 = asyncio.run(run_graph(_envelope(), _task(), provider_1, tool_1))
    res_2 = asyncio.run(run_graph(_envelope(), _task(), provider_2, tool_2))

    assert res_1["status"] == res_2["status"] == "success"
    assert res_1["code"] == res_2["code"] is None
    assert res_1["text"] == res_2["text"] == "Reviewed fixture"
    assert res_1["evidence"] == res_2["evidence"] == {"source": "fixture", "value": "42"}
    assert res_1["trace"] == res_2["trace"] == ("guard", "router", "specialist", "reviewer", "success")
    assert res_1["steps_used"] == res_2["steps_used"] == 5
    assert res_1["tool_calls_used"] == res_2["tool_calls_used"] == 1
    assert res_1["tokens_used"] == res_2["tokens_used"]
    assert res_1["cost_used"] == res_2["cost_used"]


def test_graph_blocks_step_budget_at_guard() -> None:
    tool = _tool()
    envelope = _envelope(max_steps=1)
    state: graph_module._GraphState = {
        "envelope": envelope,
        "task": _task(),
        "provider": FakeProvider([_result()]),
        "tool": tool,
        "started_at": 0.0,
        "trace": ("previous_step",),
        "steps_used": 1,
        "tool_calls_used": 0,
        "tokens_used": 0,
        "cost_used": 0.0,
        "grant": None,
        "evidence": None,
        "text": None,
        "code": None,
        "reviewed_artifact": None,
    }
    result = graph_module._guard(state)

    assert result["code"] == "step_budget_exhausted"
    assert "recovery" in result["trace"]


def test_graph_blocks_token_budget_at_guard() -> None:
    tool = _tool()
    # Prompt estimation is > 1 token, setting max_tokens=1 exhausts budget pre-flight
    result = asyncio.run(
        run_graph(_envelope(max_tokens=1), _task(), FakeProvider([_result()]), tool)
    )

    assert result["status"] == "recovery"
    assert result["code"] == "token_budget_exhausted"
    assert tool.calls == 0


def test_graph_blocks_cost_budget_at_guard() -> None:
    tool = _tool()
    # Setting max_cost_usd <= 0 exhausts cost budget pre-flight
    result = asyncio.run(
        run_graph(_envelope(max_cost_usd=0.0), _task(), FakeProvider([_result()]), tool)
    )

    assert result["status"] == "recovery"
    assert result["code"] == "cost_budget_exhausted"
    assert tool.calls == 0


def test_graph_reviewer_verifies_claims_against_evidence() -> None:
    valid_claim = Claim(
        claim_id="c1",
        kind=ClaimKind.NUMERIC,
        statement="Giá trị là 42.",
        evidence_refs=("value",),
    )
    result_with_claims = ModelResult(
        text="Giá trị là 42.",
        parsed={"claims": [valid_claim.model_dump()]},
        provider="fake",
        model="fake-model",
        latency_ms=0,
        finish_reason="stop",
    )
    tool = _tool()
    result = asyncio.run(run_graph(_envelope(), _task(), FakeProvider([result_with_claims]), tool))

    assert result["status"] == "success"
    assert result["reviewed_artifact"] is not None
    assert result["reviewed_artifact"].status is ClaimStatus.ACCEPTED
    assert result["reviewed_artifact"].ledger.claims[0].status is ClaimStatus.ACCEPTED


def test_graph_reviewer_blocks_unsupported_claim() -> None:
    invalid_claim = Claim(
        claim_id="c2",
        kind=ClaimKind.NUMERIC,
        statement="Giá trị là 99.",
        evidence_refs=("value",),
    )
    result_with_claims = ModelResult(
        text="Giá trị là 99.",
        parsed={"claims": [invalid_claim.model_dump()]},
        provider="fake",
        model="fake-model",
        latency_ms=0,
        finish_reason="stop",
    )
    tool = _tool()
    result = asyncio.run(run_graph(_envelope(), _task(), FakeProvider([result_with_claims]), tool))

    assert result["status"] == "success"
    assert result["reviewed_artifact"] is not None
    assert result["reviewed_artifact"].status is ClaimStatus.BLOCKED
    assert result["reviewed_artifact"].ledger.claims[0].status is ClaimStatus.BLOCKED
    assert result["reviewed_artifact"].ledger.claims[0].block_reason == "numeric_evidence_mismatch"


def test_graph_runs_with_real_quant_risk_tool() -> None:
    tool = QuantRiskReadOnlyTool()
    envelope = _envelope()
    task = _task()
    provider = FakeProvider([_result()])

    result = asyncio.run(run_graph(envelope, task, provider, tool))

    assert result["status"] == "success"
    assert result["code"] is None
    assert result["evidence"] is not None
    assert result["evidence"]["tool_id"] == "quant.explain_risk"
    assert result["evidence"]["fitted"] == "True"
    assert "VAR đa biến" in result["evidence"]["note"]
    assert result["trace"] == ("guard", "router", "specialist", "reviewer", "success")


def test_graph_recovers_when_kill_switch_active(monkeypatch) -> None:
    monkeypatch.setenv("AGENTIC_KILL_SWITCH", "true")
    tool = _tool()
    result = asyncio.run(run_graph(_envelope(), _task(), FakeProvider([_result()]), tool))

    assert result["status"] == "recovery"
    assert result["code"] == "kill_switch_active"
    assert tool.calls == 0


def test_graph_runs_with_bctc_domain_tool() -> None:
    from risk_dashboard.modules.agentic_core.infrastructure.domain_tools import BctcResolveLineItemTool

    tool = BctcResolveLineItemTool()
    envelope = TrustedExecutionEnvelope(
        run_id="run-bctc-1",
        correlation_id="corr-1",
        idempotency_key="idemp-1",
        account_id="account-a",
        surface="bctc_workspace",
        allowed_capabilities=("financials:read",),
        budget=ExecutionBudget(),
        policy_version="v1",
        model_policy_version="v1",
        consent=ConsentSnapshot(policy_version="v1"),
        created_at="2026-08-28T12:00:00+00:00",
    )
    task = _task()
    provider = FakeProvider([_result()])

    result = asyncio.run(run_graph(envelope, task, provider, tool))

    assert result["status"] == "success"
    assert result["code"] is None
    assert result["evidence"] is not None
    assert result["evidence"]["tool_id"] == "bctc.resolve_line_item"
    assert result["evidence"]["ticker"] == "FPT"
    assert result["trace"] == ("guard", "router", "specialist", "reviewer", "success")


def test_graph_kill_switch_blocks_at_specialist(monkeypatch) -> None:
    """SEC-02: Kill switch activated after guard passes must still block at specialist."""
    call_count = 0
    original_guard = graph_module._guard

    def _guard_then_activate(state):
        nonlocal call_count
        res = original_guard(state)
        call_count += 1
        if call_count == 1:
            monkeypatch.setenv("AGENTIC_KILL_SWITCH", "true")
        return res

    monkeypatch.setattr(graph_module, "_guard", _guard_then_activate)
    tool = _tool()
    result = asyncio.run(run_graph(_envelope(), _task(), FakeProvider([_result()]), tool))

    assert result["status"] == "recovery"
    assert result["code"] == "kill_switch_active"
    assert tool.calls == 0


# ---------------------------------------------------------------------------
# Module 4: Learning Skills & Memory Breaking Tests (Pha 2)
# ---------------------------------------------------------------------------
from risk_dashboard.modules.agentic_core.application.skill_router import SkillRouter


class TestLearningSkillRouting:
    def test_skill_router_resolves_learning_skills(self) -> None:
        """SkillRouter must resolve the 6 Module 4 learning skills to their expected domain tools."""
        expected_skills = {
            "learn.explain.v1": "learning.get_context",
            "learn.socratic_hint.v1": "learning.get_quiz_item",
            "learn.formula_walkthrough.v1": "learning.get_context",
            "learn.check_misconception.v1": "learning.get_context",
            "learn.run_checkpoint.v1": "learning.grade_checkpoint",
            "learn.next_step.v1": "learning.recommend_next",
        }
        for skill_id, expected_tool_id in expected_skills.items():
            tool = SkillRouter.resolve_tool(surface="learn", operation=skill_id)
            assert tool.manifest.tool_id == expected_tool_id, (
                f"Expected skill '{skill_id}' to resolve to tool '{expected_tool_id}', "
                f"but got '{tool.manifest.tool_id}'"
            )

    def test_run_checkpoint_skill_coordination(self) -> None:
        """Checkpoint skill coordination via SkillRouter and graph execution."""
        tool = SkillRouter.resolve_tool(surface="learn", operation="learn.run_checkpoint.v1")
        envelope = TrustedExecutionEnvelope(
            run_id="run-learn-cp-1",
            correlation_id="corr-learn-cp-1",
            idempotency_key="idemp-learn-cp-1",
            account_id="account-learner-1",
            surface="learn",
            allowed_capabilities=("learn:checkpoint:grade", "learning:read"),
            budget=ExecutionBudget(),
            policy_version="v1",
            model_policy_version="v1",
            consent=ConsentSnapshot(policy_version="v1"),
            created_at="2026-08-28T12:00:00+00:00",
        )
        task = ModelTask(
            task_id="task-learn-cp-1",
            task_type="agentic_read",
            system_instructions_ref="learn.run_checkpoint.v1",
            messages=(ModelMessage(role="user", content="grade checkpoint cp_123"),),
            correlation_id="corr-learn-cp-1",
        )
        provider = FakeProvider([_result()])

        result = asyncio.run(run_graph(envelope, task, provider, tool))

        assert result["status"] == "success"
        assert result["code"] is None
        assert result["evidence"] is not None
        assert result["evidence"]["tool_id"] in ("learning.grade_checkpoint", "learning.run_checkpoint")
        assert "verified_event_id" in result["evidence"]

    def test_mastery_proposal_persists_in_agentic_core(self, tmp_path) -> None:
        """When a checkpoint passes with mastery threshold, proposal must persist in agentic_core memory."""
        from risk_dashboard.modules.agentic_core.application.memory_service import MemoryService
        from risk_dashboard.modules.agentic_core.infrastructure.sqlite_memory import SqliteMemoryRepository
        from risk_dashboard.modules.learning.application.memory_hooks import LearningMemoryGovernor
        from risk_dashboard.modules.learning.domain.entities import VerifiedEventRecord

        db_path = tmp_path / "test_memory.db"
        repo = SqliteMemoryRepository(db_path=db_path)
        memory_service = MemoryService(repository=repo)

        passed_event = VerifiedEventRecord(
            event_id="ev_pass_mastery_99",
            account_id="user_mastery_1",
            checkpoint_id="cp_mastery_1",
            lesson_id="quant_101",
            score=100,
            passed=True,
            rubric_evidence=("Passed all criteria",),
            misconceptions=(),
            created_at="2026-09-12T10:00:00Z",
        )

        if hasattr(LearningMemoryGovernor, "record_mastery_proposal"):
            item = LearningMemoryGovernor.record_mastery_proposal(
                verified_event=passed_event,
                memory_service=memory_service,
            )
        else:
            item = getattr(LearningMemoryGovernor, "record_mastery_proposal", None)

        assert item is not None, "Mastery proposal was not recorded into agentic memory service"
        memories = memory_service.list_memories(account_id="user_mastery_1", memory_type="mastery")
        assert len(memories) == 1
        assert memories[0].memory_type == "mastery"
        assert memories[0].provenance == "deterministic_checkpoint"
        assert "quant_101" in memories[0].content



