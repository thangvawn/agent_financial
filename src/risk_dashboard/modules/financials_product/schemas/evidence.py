from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict

from risk_dashboard.modules.financials_product.schemas.agent_tools import (
    CalculateRatioOutput,
    EvidenceRow,
    ProvenanceRef,
)


class BCTCEvidenceMemo(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    memo_id: str
    subject: str
    report_refs: tuple[ProvenanceRef, ...]
    scope: str
    evidence_rows: tuple[EvidenceRow, ...]
    calculations: tuple[CalculateRatioOutput, ...] = ()
    interpretations: tuple[str, ...] = ()
    unresolved_questions: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    reviewer_status: Literal["pending", "approved", "rejected"] = "pending"
    is_stale: bool = False
    expires_at: str
    created_at: str | None = None
    updated_at: str | None = None

