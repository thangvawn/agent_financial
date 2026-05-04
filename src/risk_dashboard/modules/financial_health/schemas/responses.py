from __future__ import annotations

from pydantic import BaseModel


class FinancialHealthSubScoreResponse(BaseModel):
    key: str
    label: str
    score: int
    reason: str
    improvement_hint: str


class FinancialHealthFlagResponse(BaseModel):
    code: str
    severity: str
    title: str
    description: str


class FinancialHealthActionResponse(BaseModel):
    code: str
    priority: int
    title: str
    description: str
    related_lesson_id: str | None = None
    cta_path: str | None = None


class FinancialHealthEducationalLinkResponse(BaseModel):
    kind: str
    id: str
    title: str


class FinancialHealthResponse(BaseModel):
    session_id: str
    health_score: int
    score_band: str
    guided_investing_eligible: bool
    subscores: list[FinancialHealthSubScoreResponse]
    flags: list[FinancialHealthFlagResponse]
    actions: list[FinancialHealthActionResponse]
    educational_links: list[FinancialHealthEducationalLinkResponse]
    transparency_note: str
    compliance_note: str
    computed_at: str


class FinancialHealthCoachResponse(BaseModel):
    session_id: str
    summary: str
    explanation: str
    next_small_actions: list[str]
    confidence_note: str
