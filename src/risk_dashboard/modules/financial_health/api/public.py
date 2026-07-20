from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from risk_dashboard.modules.financial_health.application.services import (
    GetFinancialHealthSnapshot,
    SubmitFinancialHealthAssessment,
)
from risk_dashboard.modules.financial_health.infrastructure.repositories.sqlite import (
    SqliteFinancialHealthInputRepository,
    SqliteFinancialHealthSnapshotRepository,
)
from risk_dashboard.modules.financial_health.schemas.requests import FinancialHealthAssessmentRequest
from risk_dashboard.modules.financial_health.schemas.responses import FinancialHealthResponse

router = APIRouter(prefix="/financial-health", tags=["Financial Health"])


def _input_repo() -> SqliteFinancialHealthInputRepository:
    return SqliteFinancialHealthInputRepository()


def _snapshot_repo() -> SqliteFinancialHealthSnapshotRepository:
    return SqliteFinancialHealthSnapshotRepository()


@router.post("/assessment", response_model=FinancialHealthResponse)
def submit_assessment(req: FinancialHealthAssessmentRequest) -> FinancialHealthResponse:
    return SubmitFinancialHealthAssessment(
        inputs=_input_repo(),
        snapshots=_snapshot_repo(),
    ).execute(req)


@router.get("", response_model=FinancialHealthResponse)
def get_financial_health(session_id: str = Query(..., min_length=8)) -> FinancialHealthResponse:
    try:
        return GetFinancialHealthSnapshot(_snapshot_repo()).execute(session_id=session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
