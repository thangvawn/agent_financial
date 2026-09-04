from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from risk_dashboard.modules.home_onboarding.application.journey_feedback import (
    record_feedback,
)
from risk_dashboard.modules.home_onboarding.infrastructure.sqlite_journey import (
    SqliteHomeCardRepository,
    SqliteHomeFeedbackRepository,
)
from risk_dashboard.modules.home_onboarding.schemas.journey import (
    HomeJourneyFeedbackRequestV1,
    NextBestActionCardV1,
    SummarySourceRefV1,
)


@pytest.fixture
def repos(tmp_path: Path):
    db_path = tmp_path / "test_journey.db"
    card_repo = SqliteHomeCardRepository(db_path)
    feedback_repo = SqliteHomeFeedbackRepository(db_path)
    return card_repo, feedback_repo


def _create_sample_card(
    card_repo: SqliteHomeCardRepository,
    card_id: str,
    account_id: str,
    expires_at: str = "2026-10-01T00:00:00Z",
) -> NextBestActionCardV1:
    card = NextBestActionCardV1(
        card_id=card_id,
        candidate_id=f"cand_{card_id}",
        action_type="open_lesson",
        target_surface="learn",
        target_ref=SummarySourceRefV1(
            surface="learn",
            resource_type="lesson",
            resource_id="101",
            resource_version=1,
        ),
        title="Lesson 101",
        why_now="Checkpoint incomplete",
        source_summary_ids=("sum_1",),
        cta_label="Start",
        cta_path="/learn?lesson=101",
        created_at="2026-09-01T00:00:00Z",
        expires_at=expires_at,
    )
    card_repo.save_selected_card(card=card, account_id=account_id)
    return card


def test_feedback_record_success_and_duplicate(repos):
    card_repo, feedback_repo = repos
    _create_sample_card(card_repo, "card_01", "acc_A")

    req = HomeJourneyFeedbackRequestV1(
        action="snooze",
        snooze_hours=24,
        idempotency_key="idemp_key_12345",
    )

    receipt1 = record_feedback(
        account_id="acc_A",
        card_id="card_01",
        request=req,
        feedback_repo=feedback_repo,
        card_repo=card_repo,
        as_of="2026-09-01T00:00:00Z",
    )
    assert receipt1.status == "recorded"

    # Duplicate call with same idempotency key
    receipt2 = record_feedback(
        account_id="acc_A",
        card_id="card_01",
        request=req,
        feedback_repo=feedback_repo,
        card_repo=card_repo,
        as_of="2026-09-01T00:00:00Z",
    )
    assert receipt2.status == "duplicate"
    assert receipt2.receipt_id == receipt1.receipt_id


def test_feedback_unknown_or_cross_account_card(repos):
    card_repo, feedback_repo = repos
    _create_sample_card(card_repo, "card_A", "acc_A")

    req = HomeJourneyFeedbackRequestV1(
        action="dismiss",
        idempotency_key="idemp_key_54321",
    )

    # Not found
    receipt_nf = record_feedback(
        account_id="acc_A",
        card_id="non_existent",
        request=req,
        feedback_repo=feedback_repo,
        card_repo=card_repo,
    )
    assert receipt_nf.status == "not_found"

    # Cross-account: acc_B tries to access card_A
    receipt_cross = record_feedback(
        account_id="acc_B",
        card_id="card_A",
        request=req,
        feedback_repo=feedback_repo,
        card_repo=card_repo,
    )
    assert receipt_cross.status == "not_found"


def test_feedback_expired_card(repos):
    card_repo, feedback_repo = repos
    _create_sample_card(
        card_repo, "card_exp", "acc_A", expires_at="2026-08-01T00:00:00Z"
    )

    req = HomeJourneyFeedbackRequestV1(
        action="complete",
        idempotency_key="idemp_key_complete",
    )

    receipt = record_feedback(
        account_id="acc_A",
        card_id="card_exp",
        request=req,
        feedback_repo=feedback_repo,
        card_repo=card_repo,
        as_of="2026-09-01T00:00:00Z",
    )
    assert receipt.status == "expired"

