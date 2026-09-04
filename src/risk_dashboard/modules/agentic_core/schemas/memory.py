from __future__ import annotations

from pydantic import BaseModel, Field


class MemoryProposal(BaseModel):
    schema_version: str = "1.0.0"
    proposal_id: str
    run_id: str
    account_id: str
    memory_type: str
    content: str
    provenance: str
    confidence: float = Field(default=1.0, ge=0, le=1)
    sensitivity: str = "normal"
    ttl_days: int | None = Field(default=None, ge=1)
    created_at: str
