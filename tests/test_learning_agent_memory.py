from __future__ import annotations

import pytest

from risk_dashboard.modules.learning.application.memory_hooks import LearningMemoryGovernor
from risk_dashboard.modules.learning.domain.entities import VerifiedEventRecord


def test_verified_checkpoint_creates_mastery_proposal() -> None:
    event = VerifiedEventRecord(
        event_id="ev_pass_01",
        account_id="user_acct_01",
        checkpoint_id="cp_01",
        lesson_id="money-basics-101",
        score=100,
        passed=True,
        rubric_evidence=("Correct",),
        misconceptions=(),
        created_at="2026-09-02T10:00:00Z",
    )

    prop = LearningMemoryGovernor.propose_mastery(verified_event=event, memory_enabled=True)
    assert prop is not None
    assert prop.account_id == "user_acct_01"
    assert prop.lesson_id == "money-basics-101"
    assert prop.verified_event_id == "ev_pass_01"
    assert prop.topic == "mastery:money-basics-101"


def test_failed_checkpoint_creates_no_mastery_proposal() -> None:
    failed_event = VerifiedEventRecord(
        event_id="ev_fail_01",
        account_id="user_acct_01",
        checkpoint_id="cp_01",
        lesson_id="money-basics-101",
        score=0,
        passed=False,
        rubric_evidence=("Wrong",),
        misconceptions=("Misunderstood cash flow",),
        created_at="2026-09-02T10:00:00Z",
    )

    prop = LearningMemoryGovernor.propose_mastery(verified_event=failed_event, memory_enabled=True)
    assert prop is None


def test_memory_disabled_creates_no_proposal() -> None:
    event = VerifiedEventRecord(
        event_id="ev_pass_02",
        account_id="user_acct_optout",
        checkpoint_id="cp_02",
        lesson_id="money-basics-101",
        score=100,
        passed=True,
        rubric_evidence=("Correct",),
        misconceptions=(),
        created_at="2026-09-02T10:00:00Z",
    )

    prop = LearningMemoryGovernor.propose_mastery(verified_event=event, memory_enabled=False)
    assert prop is None


def test_preference_requires_explicit_consent() -> None:
    # No consent
    prop_no_consent = LearningMemoryGovernor.propose_preference(
        account_id="user_01",
        preference_key="explanation_style",
        preference_value="visual",
        consent_explicit=False,
        memory_enabled=True,
    )
    assert prop_no_consent is None

    # With consent
    prop_with_consent = LearningMemoryGovernor.propose_preference(
        account_id="user_01",
        preference_key="explanation_style",
        preference_value="visual",
        consent_explicit=True,
        memory_enabled=True,
    )
    assert prop_with_consent is not None
    assert prop_with_consent.preference_key == "explanation_style"
    assert prop_with_consent.preference_value == "visual"

