from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from risk_dashboard.modules.guided_investing.application.services import (
    CreateGuidedJournalEntry,
    GetSavedGuidedPortfolio,
    CreateGuidedWatchlistItem,
    GetGuidedCompanyHealth,
    GetGuidedEligibility,
    GetGuidedInvestingHome,
    GetGuidedMarketContext,
    GetGuidedWatchlist,
    ListGuidedJournalEntries,
    ListGuidedPortfolioReviewHistory,
    ReviewGuidedPortfolio,
    ReviewGuidedWatchlist,
    SaveGuidedPortfolio,
)
from risk_dashboard.modules.guided_investing.infrastructure.repositories.sqlite import (
    SqliteGuidedJournalRepository,
    SqliteGuidedPortfolioRepository,
    SqliteGuidedWatchlistRepository,
)
from risk_dashboard.modules.guided_investing.schemas.requests import (
    GuidedJournalCreateRequest,
    GuidedPortfolioReviewRequest,
    GuidedSavePortfolioRequest,
    GuidedWatchlistItemCreateRequest,
)
from risk_dashboard.modules.guided_investing.schemas.responses import (
    GuidedCompanyHealthResponse,
    GuidedEligibilityResponse,
    GuidedInvestingHomeResponse,
    GuidedJournalEntryResponse,
    GuidedMarketContextResponse,
    GuidedPortfolioReviewResponse,
    GuidedPortfolioReviewHistoryResponse,
    GuidedSavedPortfolioResponse,
    GuidedWatchlistItemResponse,
    GuidedWatchlistReviewResponse,
)

router = APIRouter(prefix="/guided-investing", tags=["Guided Investing"])


def _watchlists() -> SqliteGuidedWatchlistRepository:
    return SqliteGuidedWatchlistRepository()


def _journals() -> SqliteGuidedJournalRepository:
    return SqliteGuidedJournalRepository()


def _portfolios() -> SqliteGuidedPortfolioRepository:
    return SqliteGuidedPortfolioRepository()


@router.get("/eligibility", response_model=GuidedEligibilityResponse)
def guided_investing_eligibility(session_id: str = Query(..., min_length=8)) -> GuidedEligibilityResponse:
    try:
        return GetGuidedEligibility().execute(user_id=session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/home", response_model=GuidedInvestingHomeResponse)
def guided_investing_home(session_id: str = Query(..., min_length=8)) -> GuidedInvestingHomeResponse:
    try:
        return GetGuidedInvestingHome(
            watchlists=_watchlists(),
            journals=_journals(),
            portfolios=_portfolios(),
        ).execute(user_id=session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/market-context", response_model=GuidedMarketContextResponse)
def guided_market_context(
    usd_vnd_rate: float | None = None,
    sbv_interest_rate_pct: float | None = None,
) -> GuidedMarketContextResponse:
    return GetGuidedMarketContext().execute(
        usd_vnd_rate=usd_vnd_rate,
        sbv_interest_rate_pct=sbv_interest_rate_pct,
    )


@router.get("/watchlist", response_model=list[GuidedWatchlistItemResponse])
def guided_watchlist(session_id: str = Query(..., min_length=8)) -> list[GuidedWatchlistItemResponse]:
    return GetGuidedWatchlist(watchlists=_watchlists()).execute(user_id=session_id)


@router.post("/watchlist/items", response_model=GuidedWatchlistItemResponse)
def guided_watchlist_add(req: GuidedWatchlistItemCreateRequest) -> GuidedWatchlistItemResponse:
    return CreateGuidedWatchlistItem(watchlists=_watchlists()).execute(
        user_id=req.session_id,
        ticker=req.ticker,
        label=req.label,
        reason_to_track=req.reason_to_track,
        theme_tag=req.theme_tag,
    )


@router.post("/watchlist/review", response_model=GuidedWatchlistReviewResponse)
def guided_watchlist_review(session_id: str = Query(..., min_length=8)) -> GuidedWatchlistReviewResponse:
    return ReviewGuidedWatchlist(watchlists=_watchlists()).execute(user_id=session_id)


@router.get("/company/{ticker}", response_model=GuidedCompanyHealthResponse)
def guided_company_health(ticker: str) -> GuidedCompanyHealthResponse:
    try:
        return GetGuidedCompanyHealth().execute(ticker=ticker)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/portfolio/review", response_model=GuidedPortfolioReviewResponse)
def guided_portfolio_review(req: GuidedPortfolioReviewRequest) -> GuidedPortfolioReviewResponse:
    return ReviewGuidedPortfolio(portfolios=_portfolios()).execute(
        user_id=req.session_id,
        holdings=[{"ticker": item.ticker, "weight_pct": item.weight_pct} for item in req.holdings],
        scenario_label=req.scenario_label,
    )


@router.get("/portfolio", response_model=GuidedSavedPortfolioResponse | None)
def guided_saved_portfolio(session_id: str = Query(..., min_length=8)) -> GuidedSavedPortfolioResponse | None:
    return GetSavedGuidedPortfolio(portfolios=_portfolios()).execute(user_id=session_id)


@router.post("/portfolio/save", response_model=GuidedSavedPortfolioResponse)
def guided_save_portfolio(req: GuidedSavePortfolioRequest) -> GuidedSavedPortfolioResponse:
    return SaveGuidedPortfolio(portfolios=_portfolios()).execute(
        user_id=req.session_id,
        name=req.name,
        holdings=[{"ticker": item.ticker, "weight_pct": item.weight_pct} for item in req.holdings],
    )


@router.get("/portfolio/history", response_model=list[GuidedPortfolioReviewHistoryResponse])
def guided_portfolio_history(session_id: str = Query(..., min_length=8)) -> list[GuidedPortfolioReviewHistoryResponse]:
    return ListGuidedPortfolioReviewHistory(portfolios=_portfolios()).execute(user_id=session_id)


@router.get("/journal", response_model=list[GuidedJournalEntryResponse])
def guided_journal(session_id: str = Query(..., min_length=8)) -> list[GuidedJournalEntryResponse]:
    return ListGuidedJournalEntries(journals=_journals()).execute(user_id=session_id)


@router.post("/journal", response_model=GuidedJournalEntryResponse)
def guided_journal_add(req: GuidedJournalCreateRequest) -> GuidedJournalEntryResponse:
    return CreateGuidedJournalEntry(journals=_journals()).execute(
        user_id=req.session_id,
        ticker=req.ticker,
        title=req.title,
        thesis=req.thesis,
        uncertainties=req.uncertainties,
        review_condition=req.review_condition,
    )
