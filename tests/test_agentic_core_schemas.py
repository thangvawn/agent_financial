from __future__ import annotations

from risk_dashboard.modules.agentic_core.schemas.artifact import AgentArtifact, ActionProposal
from risk_dashboard.modules.agentic_core.schemas.envelope import (
    ExecutionBudget,
    ResourceRef,
    TrustedExecutionEnvelope,
)
from risk_dashboard.modules.agentic_core.schemas.memory import MemoryProposal
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
    memory = MemoryProposal(
        proposal_id="memory-1",
        run_id="run-1",
        account_id="account-a",
        memory_type="goal",
        content="Learn valuation",
        provenance="user_stated",
        created_at=NOW,
    )

    for model in (envelope, artifact, proposal, memory):
        assert type(model).model_validate_json(model.model_dump_json()) == model
