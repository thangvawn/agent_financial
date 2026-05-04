from __future__ import annotations

from pydantic import BaseModel, Field


class TrustIncidentOpenRequest(BaseModel):
    source_audit_id: str | None = None
    surface: str = Field(..., min_length=2)
    topic: str | None = None
    severity: str = Field(..., pattern="^(medium|high|critical)$")
    summary: str = Field(..., min_length=8, max_length=500)
    owner_id: str | None = None
    notes: str | None = None


class TrustIncidentActionRequest(BaseModel):
    action: str = Field(..., pattern="^(investigate|mitigate|resolve|reopen|reassign)$")
    owner_id: str | None = None
    notes: str | None = None
