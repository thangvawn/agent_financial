from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from risk_dashboard.modules.agentic_core.schemas.envelope import ResourceRef


class AgentArtifact(BaseModel):
    schema_version: str = "1.0.0"
    artifact_id: str
    artifact_type: str
    domain: str
    account_id: str
    authoring_run_id: str
    source_refs: tuple[ResourceRef, ...] = ()
    claims: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    review_status: str = "draft"
    version: int = Field(default=1, ge=1)
    created_at: str
    expires_at: str | None = None


class ActionProposal(BaseModel):
    schema_version: str = "1.0.0"
    proposal_id: str
    run_id: str
    account_id: str
    operation: str
    target: ResourceRef
    payload_preview: dict[str, Any]
    risk_class: str
    requires_confirmation: bool = True
    policy_version: str
    created_at: str
    expires_at: str


class ActionReceipt(BaseModel):
    schema_version: str = "1.0.0"
    receipt_id: str
    proposal_id: str
    account_id: str
    status: str
    executed_at: str
    result_ref: ResourceRef | None = None
    error_code: str | None = None
