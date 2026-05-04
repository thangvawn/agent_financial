from __future__ import annotations

from risk_dashboard.modules.ai_assistant.domain.contracts import AssistantContextPack, ContextSignal
from risk_dashboard.modules.financial_health.infrastructure.repositories.sqlite import SqliteFinancialHealthSnapshotRepository
from risk_dashboard.modules.goals.infrastructure.repositories.sqlite import SqliteGoalHomeReader
from risk_dashboard.modules.guided_investing.infrastructure.repositories.sqlite import (
    SqliteGuidedJournalRepository,
    SqliteGuidedPortfolioRepository,
    SqliteGuidedWatchlistRepository,
)
from risk_dashboard.modules.home_onboarding.infrastructure.repositories.sqlite import SqliteOnboardingProfileRepository
from risk_dashboard.modules.learning.infrastructure.repositories.sqlite import SqliteLearningHomeRepository


CONTEXT_BUILDER_VERSION = "context_builder_v2_bounded"


class AssistantContextBuilder:
    """Build a compact, bounded context pack.

    Keep this read-only and small. The assistant should know enough to route and
    personalize, not ingest every table row.
    """

    def build(self, *, session_id: str, surface: str) -> AssistantContextPack:
        missing: list[str] = []
        signals: list[ContextSignal] = []
        profile = SqliteOnboardingProfileRepository().get(session_id)
        if profile is None:
            missing.append("onboarding_profile")

        try:
            learning_home = SqliteLearningHomeRepository().get_home_state(user_id=session_id)
        except ValueError:
            learning_home = None
            missing.append("learning_progress")

        financial = SqliteFinancialHealthSnapshotRepository().get(session_id)
        if financial is None:
            missing.append("financial_health")

        latest_goal = SqliteGoalHomeReader().get_latest_goal_summary(session_id)
        if latest_goal is None:
            missing.append("goal")

        watchlist_count = len(SqliteGuidedWatchlistRepository().list_items(user_id=session_id))
        journal_count = len(SqliteGuidedJournalRepository().list_entries(user_id=session_id))
        saved_portfolio = SqliteGuidedPortfolioRepository().get_saved_portfolio(user_id=session_id)

        _add(signals, "persona_segment", profile.persona_segment if profile else None, "onboarding")
        _add(signals, "knowledge_level", profile.knowledge_level if profile else "beginner", "onboarding")
        _add(signals, "primary_interest", profile.primary_interest if profile else None, "onboarding")
        _add(signals, "guided_investing_eligible", bool(profile.guided_investing_eligible) if profile else False, "onboarding")
        _add(signals, "pro_eligible", bool(profile.pro_eligible) if profile else False, "onboarding")
        _add(signals, "learning_completion_pct", learning_home.completion_pct if learning_home else 0, "learning")
        _add(signals, "next_lesson_id", learning_home.next_lesson_id if learning_home else None, "learning")
        _add(signals, "health_score", financial.health_score if financial else None, "financial_health")
        _add(signals, "health_score_band", financial.score_band if financial else None, "financial_health")
        _add(signals, "goal_name", latest_goal[0].goal_name if latest_goal else None, "goals")
        _add(signals, "goal_feasibility", latest_goal[1].feasibility_band if latest_goal else None, "goals")
        _add(signals, "watchlist_count", watchlist_count, "guided_investing")
        _add(signals, "journal_count", journal_count, "guided_investing")
        _add(signals, "has_saved_portfolio", saved_portfolio is not None, "guided_investing")

        compact_context = {
            "persona_segment": profile.persona_segment if profile else None,
            "knowledge_level": profile.knowledge_level if profile else "beginner",
            "primary_interest": profile.primary_interest if profile else None,
            "guided_investing_eligible": bool(profile.guided_investing_eligible) if profile else False,
            "pro_eligible": bool(profile.pro_eligible) if profile else False,
            "learning": {
                "path_id": learning_home.path_id if learning_home else None,
                "next_lesson_id": learning_home.next_lesson_id if learning_home else None,
                "completed_lessons": learning_home.completed_lessons if learning_home else 0,
                "completion_pct": learning_home.completion_pct if learning_home else 0,
            },
            "financial_health": {
                "score_band": financial.score_band if financial else None,
                "health_score": financial.health_score if financial else None,
                "guided_eligible": bool(financial.guided_investing_eligible) if financial else False,
            },
            "goal": {
                "goal_id": latest_goal[0].goal_id if latest_goal else None,
                "goal_name": latest_goal[0].goal_name if latest_goal else None,
                "feasibility_band": latest_goal[1].feasibility_band if latest_goal else None,
            },
            "guided": {
                "watchlist_count": watchlist_count,
                "journal_count": journal_count,
                "has_saved_portfolio": saved_portfolio is not None,
            },
        }
        return AssistantContextPack(
            user_id=session_id,
            surface=surface,
            knowledge_level=profile.knowledge_level if profile else "beginner",
            persona_segment=profile.persona_segment if profile else None,
            signals=tuple(signals),
            compact_context=compact_context,
            missing_context=tuple(dict.fromkeys(missing)),
            freshness="fresh",
        )


def _add(signals: list[ContextSignal], key: str, value: object, source: str) -> None:
    if value is not None:
        signals.append(ContextSignal(key=key, value=value, source=source, freshness="fresh"))
