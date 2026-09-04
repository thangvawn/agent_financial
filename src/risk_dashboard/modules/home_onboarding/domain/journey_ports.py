from __future__ import annotations

from typing import Protocol

from risk_dashboard.modules.home_onboarding.schemas.journey import (
    HomeDomainSummaryV1,
    HomeJourneyFeedbackReceiptV1,
    NextBestActionCardV1,
)


class HomeSummaryReader(Protocol):
    surface: str

    def list_reviewed_summaries(
        self, *, account_id: str, scopes: tuple[str, ...], as_of: str, limit: int = 4
    ) -> tuple[HomeDomainSummaryV1, ...]: ...


class HomeFeedbackRepository(Protocol):
    def has_already_dismissed(self, *, account_id: str, candidate_id: str) -> bool: ...

    def is_snoozed(self, *, account_id: str, candidate_id: str, as_of: str) -> bool: ...

    def get_dismissed_candidate_ids(self, *, account_id: str) -> tuple[str, ...]: ...

    def get_snoozed_candidates(self, *, account_id: str, as_of: str) -> dict[str, str]: ...

    def record_feedback(
        self,
        *,
        receipt: HomeJourneyFeedbackReceiptV1,
        account_id: str,
        action: str,
        snooze_until: str | None = None,
        idempotency_key: str = "",
    ) -> HomeJourneyFeedbackReceiptV1: ...


class HomeCardRepository(Protocol):
    def save_selected_card(
        self,
        *,
        card: NextBestActionCardV1,
        account_id: str,
        policy_version: str = "home-ranking-v1",
    ) -> None: ...

    def get_active_card(
        self, *, account_id: str, as_of: str
    ) -> NextBestActionCardV1 | None: ...

    def get_card_by_id(
        self, *, card_id: str, account_id: str
    ) -> NextBestActionCardV1 | None: ...

