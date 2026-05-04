from __future__ import annotations

from pydantic import BaseModel


class GoalActionResponse(BaseModel):
    code: str
    priority: int
    title: str
    description: str
    cta_path: str


class GoalSummaryResponse(BaseModel):
    goal_id: str
    goal_name: str
    goal_type: str
    target_amount: float
    current_amount: float
    currency: str
    feasibility_band: str
    monthly_contribution_needed: float
    reminder_status: str | None = None
    next_reminder_at: str | None = None


class GoalResponse(BaseModel):
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
    reminder_status: str | None = None
    next_reminder_at: str | None = None
    actions: list[GoalActionResponse]
    educational_links: list[dict[str, str]]


class GoalPlannerResponse(BaseModel):
    goal_id: str
    summary: str
    feasibility_explanation: str
    trade_offs: list[str]
    next_steps: list[str]
    recommended_module: str
