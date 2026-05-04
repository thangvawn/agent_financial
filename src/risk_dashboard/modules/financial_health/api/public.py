from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from risk_dashboard.modules.ai_assistant.application.services import RespondWithAssistant
from risk_dashboard.modules.ai_assistant.infrastructure.repositories.sqlite import SqliteAssistantConversationRepository
from risk_dashboard.modules.financial_health.application.services import (
    GetFinancialHealthSnapshot,
    SubmitFinancialHealthAssessment,
)
from risk_dashboard.modules.financial_health.infrastructure.repositories.sqlite import (
    SqliteFinancialHealthInputRepository,
    SqliteFinancialHealthSnapshotRepository,
)
from risk_dashboard.modules.financial_health.schemas.requests import FinancialHealthAssessmentRequest
from risk_dashboard.modules.financial_health.schemas.responses import (
    FinancialHealthCoachResponse,
    FinancialHealthResponse,
)

router = APIRouter(prefix="/financial-health", tags=["Financial Health"])


def _input_repo() -> SqliteFinancialHealthInputRepository:
    return SqliteFinancialHealthInputRepository()


def _snapshot_repo() -> SqliteFinancialHealthSnapshotRepository:
    return SqliteFinancialHealthSnapshotRepository()


def _assistant() -> RespondWithAssistant:
    return RespondWithAssistant(conversations=SqliteAssistantConversationRepository())


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


@router.post("/coach", response_model=FinancialHealthCoachResponse)
def financial_health_coach(
    session_id: str = Query(..., min_length=8),
    focus: str | None = Query(default=None, max_length=100),
) -> FinancialHealthCoachResponse:
    try:
        reply = _assistant().execute(
            session_id=session_id,
            surface="financial_health",
            prompt="",
            role_hint="coach",
            focus=focus,
        )
        return FinancialHealthCoachResponse(
            session_id=session_id,
            summary=reply.summary,
            explanation=reply.explanation,
            next_small_actions=[reply.next_step],
            confidence_note=reply.confidence_note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
