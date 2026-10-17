from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from risk_dashboard.modules.agentic_core.schemas.artifact import ActionProposal, AgentArtifact
from risk_dashboard.modules.agentic_core.schemas.envelope import ResourceRef


class AgentRunRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    operation: str
    surface: str
    resource_refs: tuple[ResourceRef, ...] = ()
    locale: str = "vi-VN"
    task_input: dict[str, Any] | None = None
    # Compatibility alias used by the earlier agent-run API contract.
    input_parameters: dict[str, Any] | None = None
    # A client supplied key makes retries safe.  The service generates an
    # internal key when callers omit it, so existing clients remain valid.
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)


class AgentRunResponseV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    run_id: str
    status: str
    artifact: AgentArtifact | None = None
    action_proposal: ActionProposal | None = None
    # These fields expose the result without forcing clients to make a second
    # trace/artifact request.  They are optional for backwards compatibility.
    text: str | None = None
    evidence: dict[str, Any] | None = None
    reviewed_artifact: dict[str, Any] | None = None


class EditMemoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str = Field(min_length=1)
