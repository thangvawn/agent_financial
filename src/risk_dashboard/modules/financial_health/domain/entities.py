from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class FinancialHealthInput:
    session_id: str
    monthly_income_range: str
    income_stability_level: str
    expense_discipline_level: str
    emergency_fund_months_band: str
    monthly_debt_payment_ratio_band: str
    savings_rate_band: str
    liquidity_stress_level: str
    has_basic_insurance: bool
    has_high_interest_debt: bool
    wants_to_start_investing: bool
    created_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class FinancialHealthSubScore:
    key: str
    label: str
    score: int
    reason: str
    improvement_hint: str


@dataclass(frozen=True)
class FinancialHealthFlag:
    code: str
    severity: str
    title: str
    description: str


@dataclass(frozen=True)
class FinancialHealthAction:
    code: str
    priority: int
    title: str
    description: str
    related_lesson_id: str | None = None
    cta_path: str | None = None


@dataclass(frozen=True)
class FinancialHealthSnapshot:
    session_id: str
    health_score: int
    score_band: str
    guided_investing_eligible: bool
    subscores: list[FinancialHealthSubScore]
    flags: list[FinancialHealthFlag]
    actions: list[FinancialHealthAction]
    educational_links: list[dict[str, str]]
    transparency_note: str
    compliance_note: str
    computed_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class FinancialHealthCoachReply:
    summary: str
    explanation: str
    next_small_actions: list[str]
    confidence_note: str
