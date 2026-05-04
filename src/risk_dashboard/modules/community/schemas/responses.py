from __future__ import annotations

from pydantic import BaseModel


class CommunitySpaceResponse(BaseModel):
    space_id: str
    space_type: str
    title: str
    description: str
    status: str
    visibility: str
    trust_note: str
    join_hint: str
    icon_key: str = ""
    is_joined: bool = False
    is_recommended: bool = False
    member_count: int = 0
    post_count: int = 0


class CommunityMembershipResponse(BaseModel):
    space_id: str
    role: str
    status: str
    joined_at: str


class CommunityDisclaimerResponse(BaseModel):
    title: str
    short_text: str
    full_text: str
    severity: str


class CommunityContextualExplainerResponse(BaseModel):
    explainer_id: str
    title: str
    body: list[str]
    linked_lesson_ids: list[str]
    guardrail_note: str


class CommunityPostResponse(BaseModel):
    post_id: str
    space_id: str
    user_id: str
    post_type: str
    title: str
    body: str
    moderation_status: str
    moderation_labels: list[str] = []
    moderation_message: str | None = None
    created_at: str
    updated_at: str
    comments: list["CommunityCommentResponse"] = []


class CommunityCommentResponse(BaseModel):
    comment_id: str
    post_id: str
    user_id: str
    body: str
    parent_comment_id: str | None = None
    thread_depth: int = 0
    moderation_status: str
    moderation_labels: list[str] = []
    moderation_message: str | None = None
    created_at: str
    updated_at: str
    replies: list["CommunityCommentResponse"] = []


class CommunityChallengeProgressResponse(BaseModel):
    challenge_id: str
    status: str
    progress_pct: int
    last_active_at: str


class CommunityNotificationResponse(BaseModel):
    notification_id: str
    notification_type: str
    title: str
    message: str
    cta_path: str
    related_space_id: str | None = None
    status: str
    created_at: str
    updated_at: str
    next_reminder_at: str | None = None


class CommunityModerationQueueItemResponse(BaseModel):
    event_id: str
    content_type: str
    content_id: str
    user_id: str
    decision: str
    ai_risk_labels: list[str]
    notes: str | None = None
    created_at: str
    content_preview: str
    space_id: str | None = None


class CommunityReputationResponse(BaseModel):
    learning_credibility_score: int
    contribution_quality_score: int
    moderation_strike_count: int
    reputation_band: str
    trust_note: str


class CommunityStatsResponse(BaseModel):
    active_members: str
    active_members_delta: str
    discussions_today: int
    discussions_delta: str
    watchlists_shared: str
    watchlists_delta: str
    questions_answered: int
    questions_delta: str
    moderation_status: str
    moderation_note: str


class CommunityTopContributorResponse(BaseModel):
    rank: int
    user_id: str
    display_name: str
    role_badge: str
    points: int


class CommunityTrendingTopicResponse(BaseModel):
    topic_id: str
    label: str
    post_count: str


class CommunityEventResponse(BaseModel):
    event_id: str
    title: str
    schedule: str
    cta_label: str


class CommunitySavedDiscussionResponse(BaseModel):
    discussion_id: str
    title: str
    snippet: str


class CommunityHomeResponse(BaseModel):
    spaces: list[CommunitySpaceResponse]
    memberships: list[CommunityMembershipResponse]
    reputation: CommunityReputationResponse
    policy_highlights: list[str]
    recommended_space_ids: list[str]
    challenge_progress: list[CommunityChallengeProgressResponse]
    notifications: list[CommunityNotificationResponse]
    confidence_label: str = "moderate_confidence"
    what_this_is: str = ""
    what_this_is_not: str = ""
    disclaimer: CommunityDisclaimerResponse | None = None
    contextual_explainer: CommunityContextualExplainerResponse | None = None
    # --- New enriched fields ---
    stats: CommunityStatsResponse | None = None
    top_contributors: list[CommunityTopContributorResponse] = []
    trending_topics: list[CommunityTrendingTopicResponse] = []
    community_events: list[CommunityEventResponse] = []
    saved_discussions: list[CommunitySavedDiscussionResponse] = []
