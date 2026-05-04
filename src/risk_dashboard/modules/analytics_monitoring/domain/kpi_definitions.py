from __future__ import annotations

KPI_EVENT_MAP: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("onboarding_started_count", ("onboarding_started",)),
    ("onboarding_completed_count", ("onboarding_completed",)),
    ("financial_health_completion_count", ("financial_health_input_completed",)),
    ("goal_created_count", ("goal_created",)),
    ("learning_lesson_completed_count", ("learning_lesson_completed",)),
    ("guided_market_context_view_count", ("guided_market_context_viewed",)),
    ("insight_open_count", ("insight_card_opened",)),
    ("community_join_count", ("community_space_joined",)),
    ("pro_experiment_run_count", ("pro_lab_experiment_run",)),
)


SUPPORTED_WINDOW_GRAINS = {"hour", "day", "week"}
