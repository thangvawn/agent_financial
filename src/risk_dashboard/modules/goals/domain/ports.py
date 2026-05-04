from __future__ import annotations

from abc import ABC, abstractmethod

from risk_dashboard.modules.financial_health.domain.entities import FinancialHealthSnapshot
from risk_dashboard.modules.goals.domain.entities import Goal, GoalCheckIn, GoalReminderState, GoalSnapshot


class GoalRepository(ABC):
    @abstractmethod
    def save(self, goal: Goal) -> Goal:
        raise NotImplementedError

    @abstractmethod
    def get(self, goal_id: str) -> Goal | None:
        raise NotImplementedError

    @abstractmethod
    def list_by_user(self, user_id: str) -> list[Goal]:
        raise NotImplementedError


class GoalSnapshotRepository(ABC):
    @abstractmethod
    def save(self, snapshot: GoalSnapshot) -> GoalSnapshot:
        raise NotImplementedError

    @abstractmethod
    def get(self, goal_id: str) -> GoalSnapshot | None:
        raise NotImplementedError

    @abstractmethod
    def list_by_user(self, user_id: str) -> list[GoalSnapshot]:
        raise NotImplementedError


class GoalHomeReader(ABC):
    @abstractmethod
    def get_latest_goal_summary(self, user_id: str) -> tuple[Goal, GoalSnapshot] | None:
        raise NotImplementedError


class GoalCheckInRepository(ABC):
    @abstractmethod
    def save(self, checkin: GoalCheckIn) -> GoalCheckIn:
        raise NotImplementedError


class GoalReminderRepository(ABC):
    @abstractmethod
    def save(self, reminder: GoalReminderState) -> GoalReminderState:
        raise NotImplementedError

    @abstractmethod
    def get(self, goal_id: str) -> GoalReminderState | None:
        raise NotImplementedError


class FinancialHealthReader(ABC):
    @abstractmethod
    def get(self, session_id: str) -> FinancialHealthSnapshot | None:
        raise NotImplementedError
