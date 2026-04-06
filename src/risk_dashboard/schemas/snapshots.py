from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class MacroFeatures(BaseModel):
    usd_vnd_rate: float
    usd_vnd_1m_change_pct: float
    sbv_interest_rate_pct: float
    cpi_yoy_pct: float | None = None
    fdi_disbursement_yoy_pct: float | None = None


class MarketFeatures(BaseModel):
    vn_index: float
    volume_1w_trend_pct: float


class DailyFeatureRow(BaseModel):
    """Một dòng feature sau ETL — đầu vào cho quant + agents."""

    date: date
    market: MarketFeatures
    macro: MacroFeatures
    model_config = {"frozen": True}


class TargetHorizons(BaseModel):
    """Xác suất / kỳ vọng theo chân hướng (tuần chỉnh trong engine)."""

    p_decline_1w: float = Field(ge=0.0, le=1.0)
    p_decline_2w: float = Field(ge=0.0, le=1.0)
    p_decline_1m: float = Field(ge=0.0, le=1.0)
    expected_drawdown_pct: float


class HorizonBacktestMetrics(BaseModel):
    auc: float | None = None
    brier: float | None = None
    precision_high_risk: float | None = None


class ShapContribution(BaseModel):
    feature_name: str
    share: float = Field(ge=0.0, le=1.0)
    direction: Literal["increases_risk", "decreases_risk"]


class VarSummary(BaseModel):
    """Tóm tắt VAR — đủ cho dashboard, không lưu toàn bộ ma trận."""

    fitted: bool
    n_obs: int
    max_lag: int
    note: str = ""


class BacktestSummary(BaseModel):
    last_auc: float | None = None
    last_brier: float | None = None
    window_label: str = "rolling_holdout"
    metrics_by_horizon: dict[str, HorizonBacktestMetrics] = Field(default_factory=dict)


class QuantProvenance(BaseModel):
    panel_rows: int
    benchmark_dir: str | None = None
    benchmark_sources: dict[str, str] = Field(default_factory=dict)
    train_feature_count_by_horizon: dict[str, int] = Field(default_factory=dict)
    train_feature_names_by_horizon: dict[str, list[str]] = Field(default_factory=dict)
    estimator_params_by_horizon: dict[str, dict[str, float | int | bool | None]] = Field(default_factory=dict)


class QuantEngineOutput(BaseModel):
    run_id: str
    as_of: datetime
    model_version: str
    decision_score: float = Field(ge=0.0, le=1.0)
    risk_score_2w: float = Field(ge=0.0, le=1.0)
    risk_regime: Literal["low", "neutral", "high", "very_high"]
    horizons: TargetHorizons
    shap_top: list[ShapContribution]
    var_summary: VarSummary
    backtest: BacktestSummary
    dominant_feature: str
    narrative_inputs: dict[str, float | str]
    provenance: QuantProvenance

    @field_validator("shap_top")
    @classmethod
    def shap_sums_to_one(cls, v: list[ShapContribution]) -> list[ShapContribution]:
        if not v:
            return v
        s = sum(x.share for x in v)
        if abs(s - 1.0) > 0.05:
            raise ValueError("shap_top shares must sum to ~1.0")
        return v


class NarrativeBundle(BaseModel):
    headline: str
    body: str
    bullet_highlights: list[str] = Field(default_factory=list, max_length=5)
    verification_flag: bool
    mobile_one_liner: str


class ReviewResult(BaseModel):
    ok: bool
    mismatches: list[str] = Field(default_factory=list)


class EODRunManifest(BaseModel):
    run_id: str
    as_of: date
    quant: QuantEngineOutput
    narrative: NarrativeBundle
    review: ReviewResult
