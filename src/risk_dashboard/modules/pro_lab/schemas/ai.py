from __future__ import annotations

from pydantic import BaseModel, Field


class StrategyCopilotRequest(BaseModel):
    idea: str = Field(..., min_length=4, max_length=1500)
    market: str = Field(default="Vietnam equities")
    horizon: str = Field(default="monthly")
    risk_budget_pct: float = Field(default=2.0, ge=0.1, le=20.0)


class StrategyCopilotResponse(BaseModel):
    strategy_name: str
    market: str
    universe: list[str]
    signal_stack: list[str]
    risk_rules: list[str]
    validation_queue: list[str]
    rationale: str
    horizon: str
    confidence: str


class SwarmCommitteeRequest(BaseModel):
    strategy_brief: str = Field(..., min_length=10, max_length=3000)
    review_focus: str = Field(default="overfit, liquidity, benchmark gap, execution assumptions")
    market: str = Field(default="Vietnam equities")


class SwarmAgentMemo(BaseModel):
    role: str
    stance: str
    memo: str
    key_concerns: list[str]


class SwarmCommitteeResponse(BaseModel):
    consensus: str
    confidence: str
    memos: list[SwarmAgentMemo]
    decision_summary: str
    next_actions: list[str]


class BacktestCritiqueRequest(BaseModel):
    strategy_name: str
    sharpe: float | None = None
    cagr_pct: float | None = None
    max_drawdown_pct: float | None = None
    win_rate_pct: float | None = None
    sample_size: int | None = None
    notes: str = Field(default="")


class BacktestCritiqueResponse(BaseModel):
    overall_grade: str
    red_flags: list[str]
    strengths: list[str]
    additional_validation: list[str]
    interpretation: str


class AIHealthResponse(BaseModel):
    configured: bool
    provider: str
    model: str | None = None
