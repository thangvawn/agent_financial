from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class CommunitySpace:
    space_id: str
    space_type: str
    title: str
    description: str
    status: str
    visibility: str
    persona_tags: tuple[str, ...] = ()
    learning_path_id: str | None = None
    goal_tag: str | None = None
    icon_key: str = ""
    trust_note: str = ""
    join_hint: str = ""


@dataclass
class CommunityMembership:
    space_id: str
    user_id: str
    role: str = "member"
    joined_at: str = field(default_factory=utc_now_iso)
    status: str = "active"


@dataclass
class CommunityPost:
    post_id: str
    space_id: str
    user_id: str
    post_type: str
    title: str
    body: str
    linked_lesson_id: str | None = None
    linked_goal_id: str | None = None
    linked_case_id: str | None = None
    moderation_status: str = "published"
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)


@dataclass
class CommunityComment:
    comment_id: str
    post_id: str
    user_id: str
    body: str
    parent_comment_id: str | None = None
    thread_depth: int = 0
    moderation_status: str = "published"
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class CommunityModerationDecision:
    decision: str
    labels: tuple[str, ...]
    explanation: str
    escalation_level: int


@dataclass(frozen=True)
class CommunityModerationEvent:
    event_id: str
    content_type: str
    content_id: str
    user_id: str
    ai_risk_labels: tuple[str, ...]
    decision: str
    reviewer_id: str | None = None
    notes: str | None = None
    created_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class CommunityChallengeProgress:
    challenge_id: str
    user_id: str
    status: str
    progress_pct: int
    last_active_at: str


@dataclass(frozen=True)
class CommunityNotificationState:
    notification_id: str
    user_id: str
    notification_type: str
    title: str
    message: str
    cta_path: str
    related_space_id: str | None
    status: str
    created_at: str
    updated_at: str
    next_reminder_at: str | None = None


@dataclass(frozen=True)
class CommunityReputation:
    user_id: str
    learning_credibility_score: int
    contribution_quality_score: int
    moderation_strike_count: int
    reputation_band: str
    trust_note: str
    updated_at: str = field(default_factory=utc_now_iso)
