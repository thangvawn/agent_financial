from __future__ import annotations

from abc import ABC, abstractmethod

from risk_dashboard.modules.guided_investing.domain.entities import (
    GuidedJournalEntry,
    GuidedPortfolioReviewRecord,
    GuidedSavedPortfolio,
    GuidedWatchlistItem,
)


class GuidedWatchlistRepository(ABC):
    @abstractmethod
    def list_items(self, *, user_id: str) -> list[GuidedWatchlistItem]:
        raise NotImplementedError

    @abstractmethod
    def save_item(self, item: GuidedWatchlistItem) -> GuidedWatchlistItem:
        raise NotImplementedError


class GuidedJournalRepository(ABC):
    @abstractmethod
    def list_entries(self, *, user_id: str) -> list[GuidedJournalEntry]:
        raise NotImplementedError

    @abstractmethod
    def save_entry(self, entry: GuidedJournalEntry) -> GuidedJournalEntry:
        raise NotImplementedError


class GuidedPortfolioRepository(ABC):
    @abstractmethod
    def get_saved_portfolio(self, *, user_id: str) -> GuidedSavedPortfolio | None:
        raise NotImplementedError

    @abstractmethod
    def save_portfolio(self, portfolio: GuidedSavedPortfolio) -> GuidedSavedPortfolio:
        raise NotImplementedError

    @abstractmethod
    def list_review_history(self, *, user_id: str) -> list[GuidedPortfolioReviewRecord]:
        raise NotImplementedError

    @abstractmethod
    def save_review_record(self, record: GuidedPortfolioReviewRecord) -> GuidedPortfolioReviewRecord:
        raise NotImplementedError
