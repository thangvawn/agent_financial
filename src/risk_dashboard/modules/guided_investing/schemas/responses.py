from __future__ import annotations

from pydantic import BaseModel


class GuidedEligibilityResponse(BaseModel):
    eligible: bool
    reasons: list[str]
    next_step_title: str
    next_step_path: str
    caution: str


class GuidedMarketDriverResponse(BaseModel):
    label: str
    share_pct: float
    direction: str


class GuidedDisclaimerResponse(BaseModel):
    title: str
    short_text: str
    full_text: str
    severity: str


class GuidedContextualExplainerResponse(BaseModel):
    explainer_id: str
    title: str
    body: list[str]
    linked_lesson_ids: list[str]
    guardrail_note: str


class GuidedMarketContextResponse(BaseModel):
    risk_regime: str
    decision_score_pct: float
    expected_drawdown_pct: float
    headline: str
    summary: str
    so_what: str
    now_what: str
    caution: str
    data_freshness: str
    confidence_label: str = "moderate_confidence"
    what_this_is: str = ""
    what_this_is_not: str = ""
    drivers: list[GuidedMarketDriverResponse]
    scenario_note: str | None = None
    disclaimer: GuidedDisclaimerResponse | None = None
    contextual_explainer: GuidedContextualExplainerResponse | None = None


class GuidedWatchlistItemResponse(BaseModel):
    item_id: str
    ticker: str
    label: str
    reason_to_track: str
    theme_tag: str | None = None


class GuidedFlagResponse(BaseModel):
    code: str
    title: str
    detail: str


class GuidedWatchlistReviewResponse(BaseModel):
    item_count: int
    thesis_coverage_pct: int
    theme_concentration_band: str
    watchlist_hygiene_score: int
    flags: list[GuidedFlagResponse]
    next_actions: list[str]


class GuidedCompanyHealthResponse(BaseModel):
    ticker: str
    company_name: str | None = None
    industry: str | None = None
    health_band: str
    headline: str
    summary: str
    so_what: str
    now_what: str
    caution: str
    confidence_label: str = "moderate_confidence"
    risk_banner: str | None = None
    what_this_is: str = ""
    what_this_is_not: str = ""
    highlights: list[str]
    flags: list[str]
    peer_takeaways: list[str]
    disclaimer: GuidedDisclaimerResponse | None = None
    contextual_explainer: GuidedContextualExplainerResponse | None = None


class GuidedPortfolioReviewResponse(BaseModel):
    concentration_band: str
    top_holding_pct: float
    concentration_score: int
    warnings: list[str]
    next_actions: list[str]


class GuidedPortfolioHoldingResponse(BaseModel):
    ticker: str
    weight_pct: float


class GuidedSavedPortfolioResponse(BaseModel):
    portfolio_id: str
    name: str
    holdings: list[GuidedPortfolioHoldingResponse]
    created_at: str
    updated_at: str


class GuidedPortfolioReviewHistoryResponse(BaseModel):
    review_id: str
    portfolio_id: str
    scenario_label: str
    holdings: list[GuidedPortfolioHoldingResponse]
    review: GuidedPortfolioReviewResponse
    created_at: str


class GuidedJournalEntryResponse(BaseModel):
    entry_id: str
    ticker: str
    title: str
    thesis: str
    uncertainties: str
    review_condition: str
    created_at: str
    updated_at: str


class GuidedSafeReplyResponse(BaseModel):
    allowed: bool
    headline: str
    message: str
    suggested_path: str
    linked_lesson_id: str


class GuidedInvestingHomeResponse(BaseModel):
    eligibility: GuidedEligibilityResponse
    market_context: GuidedMarketContextResponse | None = None
    watchlist_review: GuidedWatchlistReviewResponse
    saved_portfolio: GuidedSavedPortfolioResponse | None = None
    latest_portfolio_review: GuidedPortfolioReviewHistoryResponse | None = None
    latest_journal: GuidedJournalEntryResponse | None = None
    next_step_title: str
    next_step_path: str
    confidence_label: str = "moderate_confidence"
    risk_banner: str | None = None
    what_this_is: str = ""
    what_this_is_not: str = ""
    disclaimer: GuidedDisclaimerResponse | None = None
    contextual_explainer: GuidedContextualExplainerResponse | None = None
