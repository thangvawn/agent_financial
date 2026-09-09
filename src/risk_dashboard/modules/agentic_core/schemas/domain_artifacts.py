from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from risk_dashboard.modules.agentic_core.schemas.envelope import ResourceRef


class NextBestActionCardV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    task_title: str
    evidence_rationale: str
    deeplink: str
    expires_at: str | None = None


class FormulaWalkthrough(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    formula_latex: str
    variables: tuple[dict[str, Any], ...] = ()
    units: dict[str, str] = Field(default_factory=dict)
    boundary_conditions: tuple[str, ...] = ()
    economic_intuition: str


class SocraticHint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    hint_level: int = Field(ge=1)
    guiding_question: str
    cause_effect_clue: str
    no_direct_answer_guarantee: bool = True


class CheckpointReview(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    checkpoint_id: str
    mastered_concepts: tuple[str, ...] = ()
    misconceptions: tuple[str, ...] = ()
    recommended_action: str


class LineItemExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    line_item_code: str
    accounting_standard: str = "VAS/IFRS"
    definition: str
    calculation_formula: str
    red_flag_warnings: tuple[str, ...] = ()


class EarningsQualityMemo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    ticker: str
    period: str
    cfo_to_net_income_ratio: float
    accruals_metric: float
    red_flags: tuple[str, ...] = ()
    conclusion_summary: str


class PreflightChecklist(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    strategy_id: str
    statistical_assumption_checks: tuple[str, ...] = ()
    data_sufficiency: bool = True
    lookahead_bias_detected: bool = False
    overfitting_risk_rating: str = "low"
    recommendations: tuple[str, ...] = ()


class BacktestCritiqueArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    backtest_id: str
    max_drawdown_pct: float
    sharpe_ratio_net_fees: float
    slippage_assumptions: dict[str, Any] = Field(default_factory=dict)
    critique_notes: tuple[str, ...] = ()


class NewsEvidenceBrief(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    cluster_id: str
    verified_facts: tuple[str, ...] = ()
    party_claims: tuple[str, ...] = ()
    hypotheses: tuple[str, ...] = ()
    importance_score: float = 0.0
    source_refs: tuple[ResourceRef, ...] = ()
    information_gaps: tuple[str, ...] = ()


class PortfolioReviewArtifactV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    portfolio_id: str
    cash_allocation_pct: float
    equity_allocation_pct: float
    portfolio_beta: float
    shock_scenarios: dict[str, float] = Field(default_factory=dict)
    concentration_warnings: tuple[str, ...] = ()
