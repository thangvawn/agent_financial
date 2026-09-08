from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ClaimKind(StrEnum):
    TEXT = "text"
    NUMERIC = "numeric"
    POLICY = "policy"


class ClaimStatus(StrEnum):
    ACCEPTED = "accepted"
    BLOCKED = "blocked"


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    claim_id: str = Field(min_length=1)
    kind: ClaimKind
    statement: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = ()


class ReviewedClaim(Claim):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: ClaimStatus
    block_reason: str | None = None


class ClaimLedger(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    claims: tuple[ReviewedClaim, ...]


class ReviewedArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    status: ClaimStatus
    text: str
    ledger: ClaimLedger
