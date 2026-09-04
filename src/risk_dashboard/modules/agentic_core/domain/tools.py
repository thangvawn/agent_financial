from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class RiskClass(StrEnum):
    READ = "read"
    PROPOSAL = "proposal"
    CONFIRMED_WRITE = "confirmed_write"
    FORBIDDEN = "forbidden"


class ToolManifest(BaseModel):
    tool_id: str
    name: str
    module: str
    risk_class: RiskClass
    version: str
    description: str
    required_capabilities: tuple[str, ...] = ()


class ToolGrant(BaseModel):
    schema_version: str = "1.0.0"
    grant_id: str
    run_id: str
    tool_id: str
    scopes: tuple[str, ...] = ()
    expires_at: str
