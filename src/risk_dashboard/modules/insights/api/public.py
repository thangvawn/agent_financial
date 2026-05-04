from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Query

from risk_dashboard.modules.insights.application.services import (
    GetCompanyInsight,
    GetInsightsDashboard,
    GetInsightsHome,
    GetScenarioInsight,
)
from risk_dashboard.modules.insights.schemas.responses import (
    InsightCardResponse,
    InsightsDashboardResponse,
    InsightsHomeResponse,
)

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get("/dashboard", response_model=InsightsDashboardResponse)
def insights_dashboard(
    session_id: str | None = Query(default=None, min_length=8),
    user_mode: Literal["investor", "learner", "advisor"] = "investor",
    range: Literal["1M", "3M", "6M", "YTD"] = "1M",  # noqa: A002
) -> InsightsDashboardResponse:
    return GetInsightsDashboard().execute(session_id=session_id, user_mode=user_mode, range_key=range)


@router.get("/home", response_model=InsightsHomeResponse)
def insights_home(
    session_id: str | None = Query(default=None, min_length=8),
    level: Literal["basic", "intermediate", "pro"] | None = None,
    ticker: str = Query(default="FPT", min_length=1),
    usd_vnd_rate: float | None = None,
    sbv_interest_rate_pct: float | None = None,
) -> InsightsHomeResponse:
    return GetInsightsHome().execute(
        session_id=session_id,
        level=level,
        ticker=ticker,
        usd_vnd_rate=usd_vnd_rate,
        sbv_interest_rate_pct=sbv_interest_rate_pct,
    )


@router.get("/company/{ticker}", response_model=InsightCardResponse)
def insight_company(
    ticker: str,
    session_id: str | None = Query(default=None, min_length=8),
    level: Literal["basic", "intermediate", "pro"] | None = None,
) -> InsightCardResponse:
    return GetCompanyInsight().execute(session_id=session_id, level=level, ticker=ticker)


@router.get("/scenario", response_model=InsightCardResponse)
def insight_scenario(
    session_id: str | None = Query(default=None, min_length=8),
    level: Literal["basic", "intermediate", "pro"] | None = None,
    usd_vnd_rate: float | None = None,
    sbv_interest_rate_pct: float | None = None,
) -> InsightCardResponse:
    return GetScenarioInsight().execute(
        session_id=session_id,
        level=level,
        usd_vnd_rate=usd_vnd_rate,
        sbv_interest_rate_pct=sbv_interest_rate_pct,
    )
