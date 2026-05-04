from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Goal:
    goal_id: str
    user_id: str
    goal_type: str
    goal_name: str
    target_amount: float
    current_amount: float
    currency: str
    base_currency: str
    deadline: str
    priority: str
    confidence_level: str
    status: str
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class GoalAction:
    code: str
    priority: int
    title: str
    description: str
    cta_path: str


@dataclass(frozen=True)
class GoalSnapshot:
    goal_id: str
    user_id: str
    gap_amount: float
    months_remaining: int
    monthly_contribution_needed: float
    feasibility_band: str
    delay_3m_monthly_needed: float
    inflation_sensitivity_band: str
    inflation_adjusted_target_estimate: float
    fx_sensitivity_band: str
    fx_upside_5pct_target: float
    fx_downside_5pct_target: float
    actions: list[GoalAction]
    educational_links: list[dict[str, str]]
    computed_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class GoalCheckIn:
    checkin_id: str
    goal_id: str
    current_amount: float
    note: str | None
    checked_in_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class GoalReminderState:
    goal_id: str
    user_id: str
    reminder_frequency: str
    last_status: str
    next_reminder_at: str
    last_reminder_at: str | None = None
    updated_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class GoalPlannerReply:
    summary: str
    feasibility_explanation: str
    trade_offs: list[str]
    next_steps: list[str]
    recommended_module: str
