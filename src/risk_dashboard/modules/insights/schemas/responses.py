from __future__ import annotations

from pydantic import BaseModel, Field


class InsightMetricResponse(BaseModel):
    label: str
    value: str


class InsightDriverResponse(BaseModel):
    label: str
    value: str
    direction: str = "neutral"


class InsightDisclaimerResponse(BaseModel):
    title: str
    short_text: str
    full_text: str
    severity: str


class InsightContextualExplainerResponse(BaseModel):
    explainer_id: str
    title: str
    body: list[str]
    linked_lesson_ids: list[str]
    guardrail_note: str


class InsightCardResponse(BaseModel):
    insight_id: str
    title: str
    level: str
    headline: str
    summary: str
    what_changed: str
    why_it_matters: str
    who_should_care: str
    what_to_learn_next: str
    action_category: str
    action_path: str | None = None
    caution: str
    freshness_status: str
    freshness_at: str | None = None
    quality_state: str
    confidence_label: str
    risk_banner: str | None = None
    what_this_is: str
    what_this_is_not: str
    metrics: list[InsightMetricResponse]
    drivers: list[InsightDriverResponse]
    disclaimer: InsightDisclaimerResponse | None = None
    contextual_explainer: InsightContextualExplainerResponse | None = None


class InsightsHomeResponse(BaseModel):
    session_id: str | None = None
    level: str
    market_regime_snapshot: InsightCardResponse
    macro_context: InsightCardResponse
    cross_asset_context: InsightCardResponse
    sector_pulse: InsightCardResponse
    company_health_insight: InsightCardResponse
    scenario_what_if: InsightCardResponse
    explainability_top_drivers: InsightCardResponse


class InsightSourceQualityResponse(BaseModel):
    source: str
    last_updated: str | None = None
    freshness_status: str
    confidence: str
    missing_fields: list[str] = Field(default_factory=list)
    stale_fields: list[str] = Field(default_factory=list)
    fallback_used: bool = False


class InsightsDataQualityResponse(BaseModel):
    overall_freshness: str
    sources: list[InsightSourceQualityResponse]
    stale_fields: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    fallback_used: list[str] = Field(default_factory=list)
    last_updated: str | None = None


class InsightsSafetyResponse(BaseModel):
    no_buy_sell_recommendation: bool = True
    disclaimer: str
    allowed_actions: list[str]
    prohibited_actions: list[str]


class MarketSummaryResponse(BaseModel):
    regime: str
    risk_level: str
    cross_asset_theme: str
    top_driver: str
    alerts_count: int
    summary: str


class SnapshotCardResponse(BaseModel):
    key: str
    label: str
    value: str
    status: str
    icon: str
    severity: str
    explanation: str


class InsightNarrativeResponse(BaseModel):
    headline: str
    summary: str
    key_points: list[str]
    caveats: list[str]
    what_to_monitor: list[str]
    confidence: str
    generated_at: str


class TrendRadarItemResponse(BaseModel):
    theme: str
    category: str
    status: str
    short_summary: str
    sparkline_series: list[float]
    signal_strength: int
    confidence: str


class CrossAssetPointResponse(BaseModel):
    date: str
    raw_value: float
    normalized_value: float


class CrossAssetSeriesResponse(BaseModel):
    asset_key: str
    label: str
    unit: str
    values: list[CrossAssetPointResponse]
    latest_change_pct: float
    normalized_base: int = 100
    freshness_status: str
    confidence: str


class CrossAssetPulseResponse(BaseModel):
    range: str
    series: list[CrossAssetSeriesResponse]


class ScenarioItemResponse(BaseModel):
    scenario_key: str
    label: str
    probability: float
    impact_level: str
    affected_themes: list[str]
    summary: str
    assumptions: list[str]
    recommended_review: str


class SectorRotationItemResponse(BaseModel):
    sector: str
    short_term_view: str
    medium_term_view: str
    relative_strength: float
    momentum_score: int
    breadth_score: int
    flow_score: int | None = None
    status: str
    explanation: str


class MacroEventResponse(BaseModel):
    event_id: str
    event_name: str
    event_time: str
    region: str
    impact_level: str
    related_themes: list[str]
    time_remaining: str
    source: str


class WatchlistThemeImpactResponse(BaseModel):
    theme: str
    affected_tickers: list[str]
    exposure_level: str
    explanation: str
    review_action: str


class WatchlistImpactResponse(BaseModel):
    state: str
    user_id: str | None = None
    message: str | None = None
    cta: str | None = None
    exposure_themes: list[str] = Field(default_factory=list)
    impacted_tickers: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)
    action_suggestions: list[str] = Field(default_factory=list)
    theme_impacts: list[WatchlistThemeImpactResponse] = Field(default_factory=list)


class LearnLinkResponse(BaseModel):
    lesson_id: str
    title: str
    concept: str
    reason: str
    difficulty: str
    estimated_minutes: int


class AiCompanionPromptResponse(BaseModel):
    label: str
    intent: str


class AiCompanionContextResponse(BaseModel):
    context_id: str
    mode: str
    suggested_prompts: list[AiCompanionPromptResponse]
    context_bundle: dict


class InsightsDashboardResponse(BaseModel):
    as_of: str
    user_mode: str
    market_summary: MarketSummaryResponse
    snapshot_cards: list[SnapshotCardResponse]
    market_narrative: InsightNarrativeResponse
    trend_radar: list[TrendRadarItemResponse]
    cross_asset_pulse: CrossAssetPulseResponse
    scenario_monitor: list[ScenarioItemResponse]
    sector_rotation: list[SectorRotationItemResponse]
    macro_calendar: list[MacroEventResponse]
    watchlist_impact: WatchlistImpactResponse
    learn_links: list[LearnLinkResponse]
    ai_companion: AiCompanionContextResponse
    safety: InsightsSafetyResponse
    data_quality: InsightsDataQualityResponse
