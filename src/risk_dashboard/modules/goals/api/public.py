from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from risk_dashboard.modules.goals.application.services import (
    CreateGoal,
    ExplainGoalPlan,
    GetGoal,
    ListGoals,
    RecordGoalCheckIn,
)
from risk_dashboard.modules.goals.infrastructure.repositories.sqlite import (
    SqliteFinancialHealthReader,
    SqliteGoalCheckInRepository,
    SqliteGoalReminderRepository,
    SqliteGoalRepository,
    SqliteGoalSnapshotRepository,
)
from risk_dashboard.modules.goals.schemas.requests import GoalCheckInRequest, GoalCreateRequest
from risk_dashboard.modules.goals.schemas.responses import GoalPlannerResponse, GoalResponse, GoalSummaryResponse

router = APIRouter(prefix="/goals", tags=["Goals"])


def _goal_repo() -> SqliteGoalRepository:
    return SqliteGoalRepository()


def _snapshot_repo() -> SqliteGoalSnapshotRepository:
    return SqliteGoalSnapshotRepository()


def _checkin_repo() -> SqliteGoalCheckInRepository:
    return SqliteGoalCheckInRepository()


def _financial_health_reader() -> SqliteFinancialHealthReader:
    return SqliteFinancialHealthReader()


def _reminder_repo() -> SqliteGoalReminderRepository:
    return SqliteGoalReminderRepository()


@router.post("", response_model=GoalResponse)
def create_goal(req: GoalCreateRequest) -> GoalResponse:
    try:
        return CreateGoal(
            goals=_goal_repo(),
            snapshots=_snapshot_repo(),
            financial_health=_financial_health_reader(),
            reminders=_reminder_repo(),
        ).execute(req)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[GoalSummaryResponse])
def list_goals(session_id: str = Query(..., min_length=8)) -> list[GoalSummaryResponse]:
    return ListGoals(
        goals=_goal_repo(),
        snapshots=_snapshot_repo(),
        reminders=_reminder_repo(),
    ).execute(user_id=session_id)


@router.get("/{goal_id}", response_model=GoalResponse)
def get_goal(goal_id: str) -> GoalResponse:
    try:
        return GetGoal(
            goals=_goal_repo(),
            snapshots=_snapshot_repo(),
            reminders=_reminder_repo(),
        ).execute(goal_id=goal_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{goal_id}/check-in", response_model=GoalResponse)
def check_in_goal(goal_id: str, req: GoalCheckInRequest) -> GoalResponse:
    try:
        return RecordGoalCheckIn(
            goals=_goal_repo(),
            snapshots=_snapshot_repo(),
            checkins=_checkin_repo(),
            financial_health=_financial_health_reader(),
            reminders=_reminder_repo(),
        ).execute(goal_id=goal_id, req=req)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{goal_id}/planner", response_model=GoalPlannerResponse)
def explain_goal_plan(goal_id: str) -> GoalPlannerResponse:
    try:
        return ExplainGoalPlan(
            goals=_goal_repo(),
            snapshots=_snapshot_repo(),
            financial_health=_financial_health_reader(),
        ).execute(goal_id=goal_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
