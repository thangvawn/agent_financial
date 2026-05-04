from __future__ import annotations

from pydantic import BaseModel, Field


class CommunityJoinRequest(BaseModel):
    session_id: str = Field(..., min_length=8)
    space_id: str = Field(..., min_length=3)


class CommunityPostCreateRequest(BaseModel):
    session_id: str = Field(..., min_length=8)
    space_id: str = Field(..., min_length=3)
    post_type: str = "discussion"
    title: str = Field(..., min_length=3, max_length=120)
    body: str = Field(..., min_length=10, max_length=3000)
    linked_lesson_id: str | None = None
    linked_goal_id: str | None = None
    linked_case_id: str | None = None


class CommunityCommentCreateRequest(BaseModel):
    session_id: str = Field(..., min_length=8)
    post_id: str = Field(..., min_length=6)
    body: str = Field(..., min_length=5, max_length=1500)
    parent_comment_id: str | None = None


class CommunityModerationReviewRequest(BaseModel):
    content_type: str = Field(..., pattern="^(post|comment)$")
    content_id: str = Field(..., min_length=6)
    action: str = Field(..., pattern="^(publish|reject)$")
    reviewer_id: str = Field(default="moderator")
    notes: str | None = None


class CommunityNotificationStateRequest(BaseModel):
    action: str = Field(..., pattern="^(read|dismiss)$")
