from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from risk_dashboard.compat import StrEnum


class RiskClass(StrEnum):
    READ = "read"
    PROPOSAL = "proposal"
    CONFIRMED_WRITE = "confirmed_write"
    FORBIDDEN = "forbidden"


class ToolManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tool_id: str
    name: str
    module: str
    risk_class: RiskClass
    version: str
    description: str
    required_capabilities: tuple[str, ...] = ()


class ToolGrant(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    grant_id: str
    run_id: str
    tool_id: str
    scopes: tuple[str, ...] = ()
    operation: str | None = None
    resource_id: str | None = None
    max_calls: int = 1
    expires_at: str
