from __future__ import annotations

from fastapi import APIRouter, HTTPException

from risk_dashboard.modules.financial_health.infrastructure.repositories.sqlite import (
    SqliteFinancialHealthSnapshotRepository,
)
from risk_dashboard.modules.goals.infrastructure.repositories.sqlite import (
    SqliteGoalHomeReader,
)
from risk_dashboard.modules.home_onboarding.application.services import (
    AnswerOnboardingQuestion,
    CompleteOnboarding,
    GetHomeState,
    StartOnboarding,
)
from risk_dashboard.modules.home_onboarding.infrastructure.repositories.sqlite import (
    SqliteHomeStateRepository,
    SqliteOnboardingProfileRepository,
    SqliteOnboardingSessionRepository,
)
from risk_dashboard.modules.learning.infrastructure.repositories.sqlite import SqliteLearningHomeRepository
from risk_dashboard.modules.home_onboarding.schemas.requests import OnboardingAnswerRequest
from risk_dashboard.modules.home_onboarding.schemas.responses import (
    HomeResponse,
    OnboardingCompleteResponse,
    OnboardingSessionResponse,
)

router = APIRouter(tags=["Onboarding"])


def _session_repo() -> SqliteOnboardingSessionRepository:
    return SqliteOnboardingSessionRepository()


def _profile_repo() -> SqliteOnboardingProfileRepository:
    return SqliteOnboardingProfileRepository()


def _home_repo() -> SqliteHomeStateRepository:
    return SqliteHomeStateRepository()


def _financial_health_snapshot_repo() -> SqliteFinancialHealthSnapshotRepository:
    return SqliteFinancialHealthSnapshotRepository()


def _learning_repo() -> SqliteLearningHomeRepository:
    return SqliteLearningHomeRepository()


def _goal_home_reader() -> SqliteGoalHomeReader:
    return SqliteGoalHomeReader()


@router.post("/onboarding/start", response_model=OnboardingSessionResponse)
def onboarding_start() -> OnboardingSessionResponse:
    return StartOnboarding(_session_repo()).execute()


@router.post("/onboarding/answer", response_model=OnboardingSessionResponse)
def onboarding_answer(req: OnboardingAnswerRequest) -> OnboardingSessionResponse:
    try:
        return AnswerOnboardingQuestion(_session_repo()).execute(
            session_id=req.session_id,
            answers=req.answers,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/onboarding/complete", response_model=OnboardingCompleteResponse)
def onboarding_complete(req: OnboardingAnswerRequest) -> OnboardingCompleteResponse:
    try:
        if req.answers:
            AnswerOnboardingQuestion(_session_repo()).execute(
                session_id=req.session_id,
                answers=req.answers,
            )
        return CompleteOnboarding(
            sessions=_session_repo(),
            profiles=_profile_repo(),
            home_states=_home_repo(),
            learning_home_writer=_learning_repo(),
        ).execute(session_id=req.session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/home/{session_id}", response_model=HomeResponse)
def personalized_home(session_id: str) -> HomeResponse:
    try:
        return GetHomeState(
            profiles=_profile_repo(),
            home_states=_home_repo(),
            financial_health_snapshots=_financial_health_snapshot_repo(),
            learning_home_reader=_learning_repo(),
            goal_home_reader=_goal_home_reader(),
        ).execute(session_id=session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
