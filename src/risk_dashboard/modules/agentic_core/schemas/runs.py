from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class AgentRun(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    run_id: str
    account_id: str
    surface: str
    status: str
    created_at: str
    updated_at: str
    correlation_id: str | None = None
    idempotency_key: str | None = None
    capability_id: str | None = None
    task_input: dict[str, Any] = Field(default_factory=dict)
    result_payload: dict[str, Any] | None = None
    usage: dict[str, Any] = Field(default_factory=dict)


class AgentStep(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    step_id: str
    run_id: str
    step_index: int = Field(ge=0)
    agent_id: str
    node_name: str
    status: str
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] = Field(default_factory=dict)
    started_at: str
    completed_at: str | None = None


class ToolCallRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    tool_call_id: str
    run_id: str
    account_id: str
    tool_name: str
    input_hash: str
    status: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    latency_ms: int = Field(default=0, ge=0)
    created_at: str
