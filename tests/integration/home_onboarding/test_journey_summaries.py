from __future__ import annotations

from unittest.mock import MagicMock
from dataclasses import dataclass

from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal, ConsentSnapshot
from risk_dashboard.modules.home_onboarding.application.journey_context import (
    build_home_journey_context,
)
from risk_dashboard.modules.home_onboarding.infrastructure.summary_adapters.learning import (
    LearningSummaryReader,
)
from risk_dashboard.modules.home_onboarding.schemas.journey import (
    HomeDomainSummaryV1,
    SummarySourceRefV1,
)


@dataclass(frozen=True)
class MockLearningHomeState:
    user_id: str
    path_id: str
    path_label: str
    next_lesson_id: str
    next_lesson_title: str
    recommendation_summary: str
    completed_lessons: int
    completion_pct: int
    updated_at: str


def test_learning_adapter_returns_reviewed_summary():
    mock_reader = MagicMock()
    mock_reader.get_home_state.return_value = MockLearningHomeState(
        user_id="acc_user_1",
        path_id="risk_foundations",
        path_label="Risk Foundations",
        next_lesson_id="lesson_var_101",
        next_lesson_title="Value at Risk Basics",
        recommendation_summary="Tiếp tục học VaR",
        completed_lessons=2,
        completion_pct=40,
        updated_at="2026-09-01T00:00:00Z",
    )

    adapter = LearningSummaryReader(reader=mock_reader)
    summaries = adapter.list_reviewed_summaries(
        account_id="acc_user_1",
        scopes=(),
        as_of="2026-09-01T00:00:00Z",
    )
    assert len(summaries) == 1
    s = summaries[0]
    assert s.surface == "learn"
    assert s.source_ref.resource_id == "lesson_var_101"
    assert s.review_status == "reviewed"
    assert s.allowed_action_type == "open_lesson"
    assert s.allowed_cta_path == "/learn?lesson=lesson_var_101"


def test_learning_adapter_graceful_on_none_reader_or_error():
    adapter = LearningSummaryReader(reader=None)
    # mock get_reader to return None
    adapter._get_reader = lambda: None
    assert adapter.list_reviewed_summaries(account_id="acc_1", scopes=(), as_of="now") == ()

    # mock exception
    failing_reader = MagicMock()
    failing_reader.get_home_state.side_effect = RuntimeError("DB error")
    adapter_err = LearningSummaryReader(reader=failing_reader)
    assert adapter_err.list_reviewed_summaries(account_id="acc_1", scopes=(), as_of="now") == ()


def test_context_builder_rejects_mismatched_account_id():
    # Adapter emits a summary belonging to another account
    spoofed_summary = HomeDomainSummaryV1(
        summary_id="spoofed_1",
        account_id="attacker_account",  # mismatch!
        surface="learn",
        kind="learning_progress",
        title="Spoofed Title",
        compact_summary="Spoofed Summary",
        source_ref=SummarySourceRefV1(
            surface="learn",
            resource_type="lesson",
            resource_id="101",
            resource_version=1,
        ),
        review_status="reviewed",
        review_policy_version="v1",
        allowed_action_type="open_lesson",
        allowed_cta_path="/learn?lesson=101",
        state="incomplete",
        created_at="2026-09-01T00:00:00Z",
        updated_at="2026-09-01T00:00:00Z",
        expires_at="2026-10-01T00:00:00Z",
    )

    mock_reader = MagicMock()
    mock_reader.surface = "learn"
    mock_reader.list_reviewed_summaries.return_value = (spoofed_summary,)

    principal = AuthPrincipal(
        account_id="victim_account",
        session_id="sess_victim",
        consent=ConsentSnapshot(
            memory=True,
            analytics=False,
            policy_version="1.0.0",
        ),
        resolved_at="2026-09-01T00:00:00Z",
    )

    context = build_home_journey_context(
        principal=principal,
        consent=(True, True),
        summary_readers=(mock_reader,),
        as_of="2026-09-01T00:00:00Z",
    )
    # The spoofed summary must be dropped by context builder ownership validation!
    assert len(context.summaries) == 0

