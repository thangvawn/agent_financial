from __future__ import annotations

from pydantic import BaseModel, Field


class GuidedWatchlistItemCreateRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=100)
    ticker: str = Field(..., min_length=1, max_length=20)
    label: str = Field(..., min_length=2, max_length=80)
    reason_to_track: str = Field(..., min_length=5, max_length=400)
    theme_tag: str | None = Field(default=None, max_length=60)


class GuidedPortfolioHoldingRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)
    weight_pct: float = Field(..., ge=0.0, le=100.0)


class GuidedPortfolioReviewRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=100)
    holdings: list[GuidedPortfolioHoldingRequest] = Field(..., min_length=1, max_length=20)
    scenario_label: str = Field(default="base_case", min_length=3, max_length=80)


class GuidedSavePortfolioRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=2, max_length=120)
    holdings: list[GuidedPortfolioHoldingRequest] = Field(..., min_length=1, max_length=20)


class GuidedJournalCreateRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=100)
    ticker: str = Field(..., min_length=1, max_length=20)
    title: str = Field(..., min_length=2, max_length=120)
    thesis: str = Field(..., min_length=5, max_length=1000)
    uncertainties: str = Field(..., min_length=5, max_length=1000)
    review_condition: str = Field(..., min_length=5, max_length=400)


class GuidedSafeChatRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=100)
    prompt: str = Field(..., min_length=2, max_length=1000)
