from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
import pytest

from risk_dashboard.modules.auth.application.services import RegisterAccount
from risk_dashboard.modules.auth.infrastructure.sqlite import (
    SqliteAccountRepository,
    SqliteAccountSessionRepository,
)
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal, ConsentSnapshot
from risk_dashboard.modules.home_onboarding.infrastructure.summary_adapters.learning import (
    LearningSummaryReader,
)
from risk_dashboard.modules.home_onboarding.infrastructure.sqlite_journey import (
    SqliteHomeCardRepository,
    SqliteHomeFeedbackRepository,
)
from risk_dashboard.modules.home_onboarding.application.journey_service import (
    get_home_journey,
)
from risk_dashboard.platform.database.config import clear_db_path_cache


@dataclass(frozen=True)
class MockLearningState:
    user_id: str
    path_id: str
    path_label: str
    next_lesson_id: str
    next_lesson_title: str
    recommendation_summary: str
    completed_lessons: int
    completion_pct: int
    updated_at: str


class MockLearningHomeReader:
    def __init__(self, state: MockLearningState) -> None:
        self._state = state

    def get_home_state(self, *, user_id: str) -> MockLearningState:
        return self._state


@pytest.fixture
def e2e_env(tmp_path: Path, monkeypatch):
    db_path = str(tmp_path / "app_state.db")
    monkeypatch.setenv("RISK_DASHBOARD_APP_STATE_DB", db_path)
    monkeypatch.setenv(
        "RISK_FLAG__MODULE__HOME_ONBOARDING__HOME_JOURNEY__V1__ENABLED", "true"
    )
    clear_db_path_cache()

    accounts = SqliteAccountRepository()
    sessions = SqliteAccountSessionRepository()
    account, session = RegisterAccount(accounts=accounts, sessions=sessions).execute(
        name="E2E Learner",
        email="learner@example.com",
        password="secure-password-e2e",
    )

    card_repo = SqliteHomeCardRepository(db_path)
    feedback_repo = SqliteHomeFeedbackRepository(db_path)

    fake_state = MockLearningState(
        user_id=account.account_id,
        path_id="risk_quant",
        path_label="Risk & Quant",
        next_lesson_id="quant_101",
        next_lesson_title="Giới thiệu VaR và CVaR",
        recommendation_summary="Học bài tiếp theo về VaR",
        completed_lessons=1,
        completion_pct=25,
        updated_at="2026-09-01T00:00:00Z",
    )
    mock_reader = LearningSummaryReader(reader=MockLearningHomeReader(fake_state))

    return {
        "account": account,
        "session": session,
        "db_path": db_path,
        "card_repo": card_repo,
        "feedback_repo": feedback_repo,
        "mock_reader": mock_reader,
    }


def test_full_home_journey_e2e_flow(e2e_env):
    async def _run():
        account = e2e_env["account"]
        card_repo = e2e_env["card_repo"]
        feedback_repo = e2e_env["feedback_repo"]
        mock_reader = e2e_env["mock_reader"]

        principal_consented = AuthPrincipal(
            account_id=account.account_id,
            session_id="sess_123",
            scopes=("me:home_journey:read", "me:home_journey:feedback"),
            consent=ConsentSnapshot(
                memory=True,
                analytics=True,
                policy_version="1.0.0",
                consented_at="2026-09-01T00:00:00Z",
            ),
            resolved_at="2026-09-01T00:00:00Z",
        )

        t0 = "2026-09-01T10:00:00Z"

        # Step 1: Initial load -> generates personalized card
        resp1 = await get_home_journey(
            principal=principal_consented,
            summary_readers=(mock_reader,),
            feedback_repo=feedback_repo,
            card_repo=card_repo,
            as_of=t0,
        )
        assert resp1.mode == "personalized"
        assert resp1.next_best_action is not None
        card = resp1.next_best_action
        assert card.target_surface == "learn"
        assert card.target_ref.resource_id == "quant_101"
        assert card.cta_path == "/learn?lesson=quant_101"

        # Step 2: User submits 24h snooze feedback
        from risk_dashboard.modules.home_onboarding.application.journey_feedback import (
            record_feedback,
        )
        from risk_dashboard.modules.home_onboarding.schemas.journey import (
            HomeJourneyFeedbackRequestV1,
        )

        receipt = record_feedback(
            account_id=account.account_id,
            card_id=card.card_id,
            request=HomeJourneyFeedbackRequestV1(
                action="snooze",
                snooze_hours=24,
                idempotency_key="idemp_e2e_snooze_01",
            ),
            feedback_repo=feedback_repo,
            card_repo=card_repo,
            as_of=t0,
        )
        assert receipt.status == "recorded"

        # Step 3: Immediate reload at t0 + 1 hour -> candidate is snoozed, mode becomes empty!
        t1 = "2026-09-01T11:00:00Z"
        resp2 = await get_home_journey(
            principal=principal_consented,
            summary_readers=(mock_reader,),
            feedback_repo=feedback_repo,
            card_repo=card_repo,
            as_of=t1,
            refresh=True,
        )
        assert resp2.mode == "empty"
        assert resp2.next_best_action is None

        # Step 4: Reload after 25 hours (t0 + 25h) -> snooze has expired!
        # Card appears again because candidate is eligible once more
        t2 = "2026-09-02T11:00:00Z"
        resp3 = await get_home_journey(
            principal=principal_consented,
            summary_readers=(mock_reader,),
            feedback_repo=feedback_repo,
            card_repo=card_repo,
            as_of=t2,
            refresh=True,
        )
        assert resp3.mode == "personalized"
        assert resp3.next_best_action is not None
        assert resp3.next_best_action.target_ref.resource_id == "quant_101"

    asyncio.run(_run())

