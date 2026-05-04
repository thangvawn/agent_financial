from __future__ import annotations

import os

from fastapi import APIRouter, Header, HTTPException, Query

from risk_dashboard.modules.community.application.services import (
    CreateCommunityComment,
    CreateCommunityPost,
    GetCommunityHome,
    JoinCommunitySpace,
    ListCommunityModerationQueue,
    ListCommunityPosts,
    ReviewCommunityModerationItem,
    UpdateCommunityNotificationState,
)
from risk_dashboard.modules.community.infrastructure.repositories.sqlite import (
    SqliteCommunityChallengeProgressRepository,
    SqliteCommunityCommentRepository,
    SqliteCommunityMembershipRepository,
    SqliteCommunityModerationRepository,
    SqliteCommunityNotificationRepository,
    SqliteCommunityPostRepository,
)
from risk_dashboard.modules.community.schemas.requests import (
    CommunityCommentCreateRequest,
    CommunityJoinRequest,
    CommunityModerationReviewRequest,
    CommunityNotificationStateRequest,
    CommunityPostCreateRequest,
)
from risk_dashboard.modules.community.schemas.responses import (
    CommunityCommentResponse,
    CommunityHomeResponse,
    CommunityMembershipResponse,
    CommunityModerationQueueItemResponse,
    CommunityNotificationResponse,
    CommunityPostResponse,
)

router = APIRouter(prefix="/community", tags=["Community"])


def _memberships() -> SqliteCommunityMembershipRepository:
    return SqliteCommunityMembershipRepository()


def _posts() -> SqliteCommunityPostRepository:
    return SqliteCommunityPostRepository()


def _comments() -> SqliteCommunityCommentRepository:
    return SqliteCommunityCommentRepository()


def _moderation() -> SqliteCommunityModerationRepository:
    return SqliteCommunityModerationRepository()


def _challenges() -> SqliteCommunityChallengeProgressRepository:
    return SqliteCommunityChallengeProgressRepository()


def _notifications() -> SqliteCommunityNotificationRepository:
    return SqliteCommunityNotificationRepository()


def _require_moderator_key(key: str | None) -> None:
    expected = os.getenv("COMMUNITY_MODERATOR_KEY", "community-dev")
    if key != expected:
        raise HTTPException(status_code=403, detail="Moderator key không hợp lệ.")


@router.get("/home", response_model=CommunityHomeResponse)
def community_home(session_id: str = Query(..., min_length=8)) -> CommunityHomeResponse:
    return GetCommunityHome(
        memberships=_memberships(),
        posts=_posts(),
        challenges=_challenges(),
        notifications=_notifications(),
    ).execute(user_id=session_id)


@router.post("/spaces/join", response_model=CommunityMembershipResponse)
def community_join(req: CommunityJoinRequest) -> CommunityMembershipResponse:
    try:
        return JoinCommunitySpace(memberships=_memberships()).execute(user_id=req.session_id, space_id=req.space_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/spaces/{space_id}/posts", response_model=list[CommunityPostResponse])
def community_posts(space_id: str) -> list[CommunityPostResponse]:
    try:
        return ListCommunityPosts(posts=_posts(), comments=_comments()).execute(space_id=space_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/spaces/posts", response_model=CommunityPostResponse)
def community_post(req: CommunityPostCreateRequest) -> CommunityPostResponse:
    try:
        return CreateCommunityPost(
            memberships=_memberships(),
            posts=_posts(),
            moderation=_moderation(),
        ).execute(
            user_id=req.session_id,
            space_id=req.space_id,
            post_type=req.post_type,
            title=req.title,
            body=req.body,
            linked_lesson_id=req.linked_lesson_id,
            linked_goal_id=req.linked_goal_id,
            linked_case_id=req.linked_case_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/spaces/comments", response_model=CommunityCommentResponse)
def community_comment(req: CommunityCommentCreateRequest) -> CommunityCommentResponse:
    try:
        return CreateCommunityComment(
            memberships=_memberships(),
            posts=_posts(),
            comments=_comments(),
            moderation=_moderation(),
        ).execute(
            user_id=req.session_id,
            post_id=req.post_id,
            body=req.body,
            parent_comment_id=req.parent_comment_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/moderation/queue", response_model=list[CommunityModerationQueueItemResponse])
def community_moderation_queue(
    space_id: str | None = Query(default=None),
    risk_label: str | None = Query(default=None),
    search: str | None = Query(default=None),
    x_community_moderator_key: str | None = Header(default=None),
) -> list[CommunityModerationQueueItemResponse]:
    _require_moderator_key(x_community_moderator_key)
    return ListCommunityModerationQueue(
        moderation=_moderation(),
        posts=_posts(),
        comments=_comments(),
    ).execute(space_id=space_id, risk_label=risk_label, search=search)


@router.post("/moderation/review", response_model=CommunityModerationQueueItemResponse)
def community_moderation_review(
    req: CommunityModerationReviewRequest,
    x_community_moderator_key: str | None = Header(default=None),
) -> CommunityModerationQueueItemResponse:
    _require_moderator_key(x_community_moderator_key)
    try:
        return ReviewCommunityModerationItem(
            moderation=_moderation(),
            posts=_posts(),
            comments=_comments(),
        ).execute(
            content_type=req.content_type,
            content_id=req.content_id,
            action=req.action,
            reviewer_id=req.reviewer_id,
            notes=req.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/notifications/{notification_id}/state", response_model=CommunityNotificationResponse)
def community_notification_state(
    notification_id: str,
    req: CommunityNotificationStateRequest,
) -> CommunityNotificationResponse:
    try:
        return UpdateCommunityNotificationState(notifications=_notifications()).execute(
            notification_id=notification_id,
            action=req.action,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
