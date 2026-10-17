from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from risk_dashboard.modules.auth.schemas.principal import ConsentSnapshot


class ResourceRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: str
    resource_id: str
    module: str


class ExecutionBudget(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    max_steps: int = Field(default=8, ge=1)
    max_tool_calls: int = Field(default=16, ge=0)
    max_tokens: int = Field(default=120_000, ge=0)
    max_wall_seconds: float = Field(default=60.0, gt=0)
    max_cost_usd: float = Field(default=0.50, ge=0)


class TrustedExecutionEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    run_id: str
    correlation_id: str
    idempotency_key: str
    account_id: str
    scopes: tuple[str, ...] = ()
    surface: str
    requested_operation: str | None = None
    requested_resource_id: str | None = None
    resource_refs: tuple[ResourceRef, ...] = ()
    locale: str = "vi-VN"
    allowed_capabilities: tuple[str, ...] = ()
    budget: ExecutionBudget = Field(default_factory=ExecutionBudget)
    policy_version: str
    model_policy_version: str
    skill_version: str | None = None
    consent: ConsentSnapshot
    memory_mode: str = "ephemeral"
    created_at: str
