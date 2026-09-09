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


class AgentRunResponseV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    run_id: str
    status: str
    artifact: AgentArtifact | None = None
    action_proposal: ActionProposal | None = None
