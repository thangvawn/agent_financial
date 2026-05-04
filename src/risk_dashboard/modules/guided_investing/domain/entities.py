from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class GuidedEligibility:
    eligible: bool
    reasons: list[str]
    next_step_title: str
    next_step_path: str
    caution: str


@dataclass(frozen=True)
class GuidedMarketDriver:
    label: str
    share_pct: float
    direction: str


@dataclass(frozen=True)
class GuidedMarketContext:
    risk_regime: str
    decision_score_pct: float
    expected_drawdown_pct: float
    headline: str
    summary: str
    so_what: str
    now_what: str
    caution: str
    data_freshness: str
    drivers: list[GuidedMarketDriver]
    scenario_note: str | None = None


@dataclass(frozen=True)
class GuidedWatchlistItem:
    item_id: str
    user_id: str
    ticker: str
    label: str
    reason_to_track: str
    theme_tag: str | None = None
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class GuidedWatchlistFlag:
    code: str
    title: str
    detail: str


@dataclass(frozen=True)
class GuidedWatchlistReview:
    item_count: int
    thesis_coverage_pct: int
    theme_concentration_band: str
    watchlist_hygiene_score: int
    flags: list[GuidedWatchlistFlag]
    next_actions: list[str]


@dataclass(frozen=True)
class GuidedCompanyHealth:
    ticker: str
    company_name: str | None
    industry: str | None
    health_band: str
    headline: str
    summary: str
    so_what: str
    now_what: str
    caution: str
    highlights: list[str]
    flags: list[str]
    peer_takeaways: list[str]


@dataclass(frozen=True)
class GuidedPortfolioReview:
    concentration_band: str
    top_holding_pct: float
    concentration_score: int
    warnings: list[str]
    next_actions: list[str]


@dataclass(frozen=True)
class GuidedPortfolioHolding:
    ticker: str
    weight_pct: float


@dataclass(frozen=True)
class GuidedSavedPortfolio:
    portfolio_id: str
    user_id: str
    name: str
    holdings: list[GuidedPortfolioHolding]
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class GuidedPortfolioReviewRecord:
    review_id: str
    portfolio_id: str
    user_id: str
    scenario_label: str
    holdings: list[GuidedPortfolioHolding]
    review: GuidedPortfolioReview
    created_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class GuidedJournalEntry:
    entry_id: str
    user_id: str
    ticker: str
    title: str
    thesis: str
    uncertainties: str
    review_condition: str
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class GuidedSafeReply:
    allowed: bool
    headline: str
    message: str
    suggested_path: str
    linked_lesson_id: str
