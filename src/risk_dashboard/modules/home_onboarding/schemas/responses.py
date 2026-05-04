from __future__ import annotations

from pydantic import BaseModel


class OnboardingSessionResponse(BaseModel):
    session_id: str
    current_step: str
    questions: tuple[str, ...]


class OnboardingCompleteResponse(BaseModel):
    session_id: str
    persona_segment: str
    primary_route: str
    guided_investing_eligible: bool
    pro_eligible: bool
    trust_message: str
    next_best_action_type: str
    next_best_action_ref: str


class HomeBlockResponse(BaseModel):
    block_id: str
    title: str
    description: str
    cta_label: str | None = None
    cta_path: str | None = None


class HomeHealthSnapshotResponse(BaseModel):
    health_score: int
    score_band: str
    guided_investing_eligible: bool
    summary: str
    top_flags: list[str]
    next_action_title: str | None = None
    next_action_path: str | None = None


class HomeGoalSnapshotResponse(BaseModel):
    goal_id: str
    goal_name: str
    goal_type: str
    current_amount: float
    target_amount: float
    currency: str
    gap_amount: float
    monthly_contribution_needed: float
    feasibility_band: str
    months_remaining: int
    reminder_status: str | None = None
    next_reminder_at: str | None = None
    summary: str
    next_action_title: str | None = None
    next_action_path: str | None = None


class HomeCommunitySnapshotResponse(BaseModel):
    recommended_space_id: str | None = None
    recommended_space_title: str | None = None
    joined_space_count: int
    challenge_id: str | None = None
    challenge_status: str | None = None
    challenge_progress_pct: int | None = None
    active_notification_count: int = 0
    next_notification_title: str | None = None
    next_notification_path: str | None = None
    summary: str
    next_action_title: str | None = None
    next_action_path: str | None = None


class HomeResponse(BaseModel):
    session_id: str
    persona_segment: str
    primary_route: str
    guided_investing_eligible: bool
    pro_eligible: bool
    next_best_action_type: str
    next_best_action_ref: str
    trust_message: str
    blocks: list[HomeBlockResponse]
    health_snapshot: HomeHealthSnapshotResponse | None = None
    goal_snapshot: HomeGoalSnapshotResponse | None = None
    community_snapshot: HomeCommunitySnapshotResponse | None = None
