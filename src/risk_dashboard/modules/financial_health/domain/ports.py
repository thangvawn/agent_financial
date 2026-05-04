from __future__ import annotations

from abc import ABC, abstractmethod

from risk_dashboard.modules.financial_health.domain.entities import FinancialHealthInput, FinancialHealthSnapshot


class FinancialHealthInputRepository(ABC):
    @abstractmethod
    def save(self, payload: FinancialHealthInput) -> FinancialHealthInput:
        raise NotImplementedError

    @abstractmethod
    def get(self, session_id: str) -> FinancialHealthInput | None:
        raise NotImplementedError


class FinancialHealthSnapshotRepository(ABC):
    @abstractmethod
    def save(self, snapshot: FinancialHealthSnapshot) -> FinancialHealthSnapshot:
        raise NotImplementedError

    @abstractmethod
    def get(self, session_id: str) -> FinancialHealthSnapshot | None:
        raise NotImplementedError
