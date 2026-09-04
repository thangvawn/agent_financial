from __future__ import annotations

import random
from typing import Any

import pytest

from risk_dashboard.modules.home_onboarding.application.journey_candidates import (
    create_candidates,
)
from risk_dashboard.modules.home_onboarding.application.journey_ranker import (
    rank_candidates,
)
from risk_dashboard.modules.home_onboarding.schemas.journey import (
    HomeDomainSummaryV1,
    JourneyContextV1,
    SummarySourceRefV1,
)


def _make_summary(
    summary_id: str,
    surface: str,
    kind: str,
    state: str,
    action_type: str = "open_lesson",
    cta_path: str = "/learn?lesson=1",
) -> HomeDomainSummaryV1:
    return HomeDomainSummaryV1(
        summary_id=summary_id,
        account_id="acc_1",
        surface=surface,  # type: ignore
        kind=kind,  # type: ignore
        title=f"Title {summary_id}",
        compact_summary=f"Summary {summary_id}",
        source_ref=SummarySourceRefV1(
            surface=surface,  # type: ignore
            resource_type="lesson",
            resource_id=summary_id,
            resource_version=1,
        ),
        review_status="reviewed",
        review_policy_version="v1",
        allowed_action_type=action_type,
        allowed_cta_path=cta_path,
        state=state,  # type: ignore
        created_at="2026-09-01T00:00:00Z",
        updated_at="2026-09-01T00:00:00Z",
        expires_at="2026-10-01T00:00:00Z",
    )


def test_empty_candidates_returns_none():
    assert rank_candidates([]) is None


def test_priority_ordering():
    s_market = _make_summary(
        "m1", "market", "market_education", "ready",
        "read_market_education", "/market/learn"
    )
    s_stale = _make_summary(
        "st1", "simulation", "stale_artifact", "stale",
        "refresh_artifact", "/simulation"
    )
    s_research = _make_summary(
        "r1", "bctc", "research_artifact", "open_question",
        "view_research_memo", "/bctc"
    )
    s_learn = _make_summary(
        "l1", "learn", "learning_progress", "incomplete",
        "open_lesson", "/learn?lesson=101"
    )

    context = JourneyContextV1(
        account_id="acc_1",
        personalization_consented=True,
        summaries=(s_market, s_stale, s_research, s_learn),
        built_at="2026-09-01T00:00:00Z",
    )
    candidates = create_candidates(context)
    winner = rank_candidates(candidates)
    assert winner is not None
    # Learn checkpoint priority 100 beats research (80), stale (60), market (20)
    assert winner["summary"].summary_id == "l1"


def test_stable_winner_across_1000_shuffles():
    candidates: list[dict[str, Any]] = [
        {
            "candidate_id": f"cand_{i:02d}",
            "priority": random.choice([20, 40, 80, 100]),
            "updated_at": "2026-09-01T00:00:00Z",
            "created_at": "2026-09-01T00:00:00Z",
        }
        for i in range(12)
    ]

    initial_winner = rank_candidates(candidates)
    assert initial_winner is not None

    for _ in range(1000):
        shuffled = list(candidates)
        random.shuffle(shuffled)
        assert rank_candidates(shuffled)["candidate_id"] == initial_winner["candidate_id"]


def test_cooldown_and_dismissed_skipped():
    s1 = _make_summary("l1", "learn", "learning_progress", "incomplete")
    s2 = _make_summary("l2", "learn", "learning_progress", "ready")

    context_full = JourneyContextV1(
        account_id="acc_1",
        personalization_consented=True,
        summaries=(s1, s2),
        built_at="2026-09-01T00:00:00Z",
    )
    candidates = create_candidates(context_full)
    cid1 = candidates[0]["candidate_id"]

    # When dismissed
    context_dismissed = JourneyContextV1(
        account_id="acc_1",
        personalization_consented=True,
        summaries=(s1, s2),
        dismissed_candidate_ids=(cid1,),
        built_at="2026-09-01T00:00:00Z",
    )
    cand_after_dismiss = create_candidates(context_dismissed)
    assert all(c["candidate_id"] != cid1 for c in cand_after_dismiss)

    # When snoozed until future
    context_snoozed = JourneyContextV1(
        account_id="acc_1",
        personalization_consented=True,
        summaries=(s1, s2),
        snoozed_until_by_candidate={cid1: "2026-09-05T00:00:00Z"},
        built_at="2026-09-01T00:00:00Z",
    )
    cand_after_snooze = create_candidates(
        context_snoozed, as_of="2026-09-02T00:00:00Z"
    )
    assert all(c["candidate_id"] != cid1 for c in cand_after_snooze)

