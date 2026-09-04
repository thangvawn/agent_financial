from __future__ import annotations

import pytest
from pydantic import ValidationError

from risk_dashboard.modules.home_onboarding.schemas.journey import (
    ExplicitHomeMemoryV1,
    HomeDomainSummaryV1,
    HomeJourneyFeedbackReceiptV1,
    HomeJourneyFeedbackRequestV1,
    HomeJourneyResponseV1,
    NextBestActionCardV1,
    SummarySourceRefV1,
)


def _make_source_ref(**kwargs) -> SummarySourceRefV1:
    defaults = {
        "schema_version": "1.0.0",
        "surface": "learn",
        "resource_type": "lesson",
        "resource_id": "lesson_101",
        "resource_version": 1,
    }
    defaults.update(kwargs)
    return SummarySourceRefV1(**defaults)


def _make_domain_summary(**kwargs) -> HomeDomainSummaryV1:
    defaults = {
        "schema_version": "1.0.0",
        "summary_id": "sum_1",
        "account_id": "acc_1",
        "surface": "learn",
        "kind": "learning_progress",
        "title": "Title 1",
        "compact_summary": "Summary 1",
        "source_ref": _make_source_ref(),
        "review_status": "reviewed",
        "review_policy_version": "policy_1",
        "allowed_action_type": "open_lesson",
        "allowed_cta_path": "/learn?lesson=101",
        "state": "incomplete",
        "created_at": "2026-09-01T00:00:00Z",
        "updated_at": "2026-09-01T00:00:00Z",
        "expires_at": "2026-10-01T00:00:00Z",
    }
    defaults.update(kwargs)
    return HomeDomainSummaryV1(**defaults)


def test_reject_unknown_schema_version():
    with pytest.raises(ValidationError):
        _make_source_ref(schema_version="2.0.0")
    with pytest.raises(ValidationError):
        _make_domain_summary(schema_version="2.0.0")


def test_reject_resource_version_less_than_one():
    with pytest.raises(ValidationError):
        _make_source_ref(resource_version=0)


def test_reject_oversized_title_and_summary():
    with pytest.raises(ValidationError):
        _make_domain_summary(title="a" * 121)
    with pytest.raises(ValidationError):
        _make_domain_summary(compact_summary="b" * 501)


def test_reject_invalid_state_and_review_status():
    with pytest.raises(ValidationError):
        _make_domain_summary(state="invalid_state")
    with pytest.raises(ValidationError):
        _make_domain_summary(review_status="unreviewed")


def test_feedback_request_validation():
    # valid
    req = HomeJourneyFeedbackRequestV1(
        action="snooze",
        snooze_hours=24,
        idempotency_key="abcdef1234",
    )
    assert req.action == "snooze"

    # invalid snooze_hours
    with pytest.raises(ValidationError):
        HomeJourneyFeedbackRequestV1(
            action="snooze",
            snooze_hours=48,  # only 24, 72, 168
            idempotency_key="abcdef1234",
        )

    # invalid idempotency_key length
    with pytest.raises(ValidationError):
        HomeJourneyFeedbackRequestV1(action="dismiss", idempotency_key="short")


def test_roundtrip_serialization():
    summary = _make_domain_summary()
    data = summary.model_dump()
    reconstructed = HomeDomainSummaryV1.model_validate(data)
    assert reconstructed.summary_id == summary.summary_id

    card = NextBestActionCardV1(
        card_id="card_1",
        candidate_id="cand_1",
        action_type="open_lesson",
        target_surface="learn",
        target_ref=_make_source_ref(),
        title="Next Lesson",
        why_now="Continue from checkpoint",
        source_summary_ids=("sum_1",),
        cta_label="Start",
        cta_path="/learn?lesson=101",
        created_at="2026-09-01T00:00:00Z",
        expires_at="2026-09-02T00:00:00Z",
    )
    card_json = card.model_dump_json()
    re_card = NextBestActionCardV1.model_validate_json(card_json)
    assert re_card.card_id == "card_1"

    resp = HomeJourneyResponseV1(
        generated_at="2026-09-01T00:00:00Z",
        mode="personalized",
        next_best_action=card,
    )
    assert resp.mode == "personalized"

    receipt = HomeJourneyFeedbackReceiptV1(
        receipt_id="rec_1",
        card_id="card_1",
        status="recorded",
        recorded_at="2026-09-01T00:00:00Z",
    )
    assert receipt.status == "recorded"

