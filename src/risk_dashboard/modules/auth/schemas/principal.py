from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ConsentSnapshot(BaseModel):
    schema_version: str = "1.0.0"
    memory: bool = False
    analytics: bool = False
    policy_version: str
    consented_at: str | None = None


class AuthPrincipal(BaseModel):
    schema_version: str = "1.0.0"
    account_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    assurance: Literal["anonymous", "session", "recent_auth"] = "session"
    scopes: tuple[str, ...] = ()
    is_anonymous: bool = False
    consent: ConsentSnapshot | None = None
    resolved_at: str
