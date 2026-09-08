from __future__ import annotations

import pytest
from pydantic import ValidationError

from risk_dashboard.modules.agentic_core.schemas.artifact import ActionProposal, ActionReceipt, AgentArtifact
from risk_dashboard.modules.agentic_core.schemas.claim import (
    Claim,
    ClaimKind,
    ClaimLedger,
    ClaimStatus,
    ReviewedArtifact,
    ReviewedClaim,
)
from risk_dashboard.modules.agentic_core.schemas.envelope import (
    ExecutionBudget,
    ResourceRef,
    TrustedExecutionEnvelope,
)
from risk_dashboard.modules.agentic_core.schemas.memory import MemoryProposal
from risk_dashboard.modules.agentic_core.schemas.requests import AgentRunRequestV1, AgentRunResponseV1
from risk_dashboard.modules.agentic_core.schemas.runs import AgentRun, AgentStep, ToolCallRecord
from risk_dashboard.modules.auth.schemas.principal import ConsentSnapshot

NOW = "2026-08-28T12:00:00+00:00"


def test_agentic_schemas_round_trip() -> None:
    resource = ResourceRef(kind="report", resource_id="report-1", module="pro_lab")
    envelope = TrustedExecutionEnvelope(
        run_id="run-1",
        correlation_id="correlation-1",
        idempotency_key="idempotency-1",
        account_id="account-a",
        surface="pro_lab",
        resource_refs=(resource,),
        budget=ExecutionBudget(),
        policy_version="v1",
        model_policy_version="v1",
        consent=ConsentSnapshot(policy_version="v1"),
        created_at=NOW,
    )
    artifact = AgentArtifact(
        artifact_id="artifact-1",
        artifact_type="analysis",
        domain="finance",
        account_id="account-a",
        authoring_run_id="run-1",
        created_at=NOW,
    )
    proposal = ActionProposal(
        proposal_id="proposal-1",
        run_id="run-1",
        account_id="account-a",
        operation="export_report",
        target=resource,
        payload_preview={},
        risk_class="proposal",
        policy_version="v1",
        created_at=NOW,
        expires_at=NOW,
    )
    receipt = ActionReceipt(
        receipt_id="rcpt-1",
        proposal_id="proposal-1",
        account_id="account-a",
        status="executed",
        executed_at=NOW,
    )
    memory = MemoryProposal(
        proposal_id="memory-1",
        run_id="run-1",
        account_id="account-a",
        memory_type="goal",
        content="Learn valuation",
        provenance="user_stated",
        created_at=NOW,
    )
    run = AgentRun(
        run_id="run-1",
        account_id="account-a",
        surface="pro_lab",
        status="accepted",
        created_at=NOW,
        updated_at=NOW,
    )
    step = AgentStep(
        step_id="step-1",
        run_id="run-1",
        step_index=0,
        agent_id="supervisor",
        node_name="guard_node",
        status="completed",
        started_at=NOW,
    )
    tool_call = ToolCallRecord(
        tool_call_id="tc-1",
        run_id="run-1",
        account_id="account-a",
        tool_name="quant.var",
        input_hash="hash-123",
        status="success",
        created_at=NOW,
    )

    for model in (envelope, artifact, proposal, receipt, memory, run, step, tool_call):
        assert type(model).model_validate_json(model.model_dump_json()) == model
        assert getattr(model, "schema_version") == "1.0.0"


def test_schema_extra_fields_forbidden() -> None:
    """Iron Rule 4: Cấm Extra Fields."""
    with pytest.raises(ValidationError):
        ResourceRef(kind="report", resource_id="r1", module="pro_lab", injected_field="malicious")  # type: ignore

    with pytest.raises(ValidationError):
        ExecutionBudget(max_steps=8, extra_step=10)  # type: ignore

    with pytest.raises(ValidationError):
        ActionReceipt(
            receipt_id="r-1",
            proposal_id="p-1",
            account_id="a-1",
            status="executed",
            executed_at=NOW,
            unauthorized_data="leak",  # type: ignore
        )


def test_client_cannot_inject_authority_fields_in_request() -> None:
    """Client request schema AgentRunRequestV1 must reject account_id/scopes injection."""
    # Valid client request
    req = AgentRunRequestV1(
        operation="analyze_risk",
        surface="pro_lab",
        resource_refs=(),
    )
    assert req.operation == "analyze_risk"

    # Attacker tries to spoof account_id
    with pytest.raises(ValidationError):
        AgentRunRequestV1(
            operation="analyze_risk",
            surface="pro_lab",
            account_id="victim_account",  # type: ignore
        )

    # Attacker tries to escalate scopes
    with pytest.raises(ValidationError):
        AgentRunRequestV1(
            operation="analyze_risk",
            surface="pro_lab",
            scopes=("admin:all",),  # type: ignore
        )

    # Attacker tries to inject allowed_capabilities
    with pytest.raises(ValidationError):
        AgentRunRequestV1(
            operation="analyze_risk",
            surface="pro_lab",
            allowed_capabilities=("quant:all",),  # type: ignore
        )


def test_models_are_frozen_immutable() -> None:
    """Iron Rule 4: ConfigDict(frozen=True)."""
    artifact = AgentArtifact(
        artifact_id="artifact-1",
        artifact_type="analysis",
        domain="finance",
        account_id="account-a",
        authoring_run_id="run-1",
        created_at=NOW,
    )
    with pytest.raises(ValidationError):
        artifact.review_status = "accepted"  # type: ignore
