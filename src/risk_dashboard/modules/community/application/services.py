from __future__ import annotations

from datetime import datetime, timedelta, timezone

from risk_dashboard.modules.analytics_monitoring.application.emitter import emit_product_event
from risk_dashboard.modules.admin_cms.application.runtime_reader import ContentOpsRuntimeReader
from risk_dashboard.modules.admin_cms.infrastructure.repositories.sqlite import SqliteAdminCmsRepository
from risk_dashboard.modules.community.domain.entities import (
    CommunityChallengeProgress,
    CommunityComment,
    CommunityMembership,
    CommunityModerationEvent,
    CommunityNotificationState,
    CommunityPost,
    utc_now_iso,
)
from risk_dashboard.modules.community.domain.policies import (
    build_reputation,
    moderate_post,
    recommend_space_ids,
)
from risk_dashboard.modules.community.domain.ports import (
    CommunityChallengeProgressRepository,
    CommunityCommentRepository,
    CommunityMembershipRepository,
    CommunityModerationRepository,
    CommunityNotificationRepository,
    CommunityPostRepository,
)
from risk_dashboard.modules.community.infrastructure.catalog import get_community_space, list_community_spaces
from risk_dashboard.modules.community.infrastructure.repositories.sqlite import (
    new_community_comment_id,
    new_community_event_id,
    new_community_post_id,
)
from risk_dashboard.modules.community.schemas.responses import (
    CommunityChallengeProgressResponse,
    CommunityCommentResponse,
    CommunityContextualExplainerResponse,
    CommunityDisclaimerResponse,
    CommunityEventResponse,
    CommunityHomeResponse,
    CommunityMembershipResponse,
    CommunityModerationQueueItemResponse,
    CommunityNotificationResponse,
    CommunityPostResponse,
    CommunityReputationResponse,
    CommunitySavedDiscussionResponse,
    CommunitySpaceResponse,
    CommunityStatsResponse,
    CommunityTopContributorResponse,
    CommunityTrendingTopicResponse,
)
from risk_dashboard.modules.trust_safety.application.services import TrustSafetyService

class GetCommunityHome:
    def __init__(
        self,
        memberships: CommunityMembershipRepository,
        posts: CommunityPostRepository,
        challenges: CommunityChallengeProgressRepository,
        notifications: CommunityNotificationRepository,
    ) -> None:
        self.memberships = memberships
        self.posts = posts
        self.challenges = challenges
        self.notifications = notifications

    def execute(self, *, user_id: str) -> CommunityHomeResponse:
        from risk_dashboard.modules.goals.infrastructure.repositories.sqlite import SqliteGoalRepository
        from risk_dashboard.modules.home_onboarding.infrastructure.repositories.sqlite import (
            SqliteOnboardingProfileRepository,
        )
        from risk_dashboard.modules.learning.infrastructure.repositories.sqlite import (
            SqliteLearningHomeRepository,
        )

        profile = SqliteOnboardingProfileRepository().get(user_id)
        memberships = self.memberships.list_memberships(user_id=user_id)
        joined_ids = {item.space_id for item in memberships}
        try:
            learning_home = SqliteLearningHomeRepository().get_home_state(user_id=user_id)
            completed_lessons = learning_home.completed_lessons
        except ValueError:
            completed_lessons = 0
        goal_count = len(SqliteGoalRepository().list_by_user(user_id))
        recommended_ids = recommend_space_ids(
            persona_segment=profile.persona_segment if profile is not None else "starter",
            has_goal=goal_count > 0,
            completed_lessons=completed_lessons,
        )
        existing_notifications = self.notifications.list_notifications(user_id=user_id, active_only=False)
        challenge_progress = _sync_challenge_progress(
            user_id=user_id,
            memberships=memberships,
            posts=self.posts,
            challenges=self.challenges,
            completed_lessons=completed_lessons,
            goal_count=goal_count,
        )
        notifications = _sync_notifications(
            user_id=user_id,
            memberships=memberships,
            challenge_progress=challenge_progress,
            recommended_ids=recommended_ids,
            goal_count=goal_count,
            existing_notifications=existing_notifications,
        )
        self.notifications.replace_notifications(user_id=user_id, notifications=notifications)
        visible_notifications = self.notifications.list_notifications(user_id=user_id, active_only=True)
        reputation = build_reputation(
            user_id=user_id,
            completed_lessons=completed_lessons,
            goal_count=goal_count,
            published_posts=self.posts.count_posts_by_status(user_id=user_id, status="published"),
            held_posts=self.posts.count_posts_by_status(user_id=user_id, status="held_for_review"),
            blocked_posts=self.posts.count_posts_by_status(user_id=user_id, status="blocked"),
        )
        runtime_reader = ContentOpsRuntimeReader()
        disclaimer = runtime_reader.get_disclaimer(surface="community", topic="community_home")
        contextual_explainer = runtime_reader.get_contextual_explainer(
            surface="community",
            trigger_key=recommended_ids[0] if recommended_ids else "community_home",
        )
        trust = TrustSafetyService()
        presentation = trust.build_presentation(
            surface="community",
            topic="community_home",
            quality_state="good",
            freshness_value=None,
            disclaimer=disclaimer,
        )
        trust.record_audit(
            actor_id=user_id,
            surface="community",
            topic="community_home",
            channel="runtime_card",
            risk_classes=tuple(
                label for label in ("missing_disclaimer" if presentation.disclaimer_injected else "",) if label
            ),
            route_decision="served_community_home",
            output_summary="community_home",
            disclaimer_injected=presentation.disclaimer_injected,
            confidence_label=presentation.confidence_label,
        )
        emit_product_event(
            event_name="community_home_viewed",
            module="community",
            surface="community",
            user_id=user_id,
            session_id=user_id,
            properties={
                "recommended_space_count": len(recommended_ids),
                "notification_count": len(visible_notifications),
            },
        )
        member_counts = _build_member_counts(memberships)
        post_counts = _build_post_counts(self.posts)
        return CommunityHomeResponse(
            spaces=[
                CommunitySpaceResponse(
                    space_id=space.space_id,
                    space_type=space.space_type,
                    title=space.title,
                    description=space.description,
                    status=space.status,
                    visibility=space.visibility,
                    trust_note=space.trust_note,
                    join_hint=space.join_hint,
                    icon_key=space.icon_key,
                    is_joined=space.space_id in joined_ids,
                    is_recommended=space.space_id in recommended_ids,
                    member_count=member_counts.get(space.space_id, 0),
                    post_count=post_counts.get(space.space_id, 0),
                )
                for space in list_community_spaces()
            ],
            memberships=[
                CommunityMembershipResponse(
                    space_id=item.space_id,
                    role=item.role,
                    status=item.status,
                    joined_at=item.joined_at,
                )
                for item in memberships
            ],
            reputation=CommunityReputationResponse(
                learning_credibility_score=reputation.learning_credibility_score,
                contribution_quality_score=reputation.contribution_quality_score,
                moderation_strike_count=reputation.moderation_strike_count,
                reputation_band=reputation.reputation_band,
                trust_note=reputation.trust_note,
            ),
            policy_highlights=_resolve_policy_highlights(),
            recommended_space_ids=recommended_ids,
            challenge_progress=[
                CommunityChallengeProgressResponse(
                    challenge_id=item.challenge_id,
                    status=item.status,
                    progress_pct=item.progress_pct,
                    last_active_at=item.last_active_at,
                )
                for item in challenge_progress
            ],
            notifications=[
                CommunityNotificationResponse(
                    notification_id=item.notification_id,
                    notification_type=item.notification_type,
                    title=item.title,
                    message=item.message,
                    cta_path=item.cta_path,
                    related_space_id=item.related_space_id,
                    status=item.status,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                    next_reminder_at=item.next_reminder_at,
                )
                for item in visible_notifications
            ],
            confidence_label=presentation.confidence_label,
            what_this_is=presentation.what_this_is,
            what_this_is_not=presentation.what_this_is_not,
            disclaimer=(
                CommunityDisclaimerResponse(
                    title=presentation.disclaimer.title,
                    short_text=presentation.disclaimer.short_text,
                    full_text=presentation.disclaimer.full_text,
                    severity=presentation.disclaimer.severity,
                )
                if presentation.disclaimer is not None
                else None
            ),
            contextual_explainer=(
                CommunityContextualExplainerResponse(
                    explainer_id=contextual_explainer.explainer_id,
                    title=contextual_explainer.title,
                    body=contextual_explainer.body,
                    linked_lesson_ids=contextual_explainer.linked_lesson_ids,
                    guardrail_note=contextual_explainer.guardrail_note,
                )
                if contextual_explainer is not None
                else None
            ),
            stats=_build_community_stats(),
            top_contributors=_build_top_contributors(),
            trending_topics=_build_trending_topics(),
            community_events=_build_community_events(),
            saved_discussions=_build_saved_discussions(),
        )


def _resolve_policy_highlights() -> list[str]:
    repo = SqliteAdminCmsRepository()
    published = repo.list_published_content(content_type="community_policy_snippet")
    highlights: list[str] = []
    for item, version in published:
        payload = version.payload
        surface = str(payload.get("surface") or "community")
        if surface != "community":
            continue
        body = str(payload.get("body") or item.title).strip()
        if body:
            highlights.append(body)
    if highlights:
        return highlights
    return [
        "Community này để học và trao đổi có kiểm soát, không phải room tín hiệu.",
        "Các bài có hô hào giao dịch, kéo room ngoài hoặc certainty claims sẽ bị chặn hoặc giữ lại review.",
        "Uy tín trong community dựa trên học tập và đóng góp chất lượng, không dựa trên độ ồn hay PnL.",
    ]


class JoinCommunitySpace:
    def __init__(self, memberships: CommunityMembershipRepository) -> None:
        self.memberships = memberships

    def execute(self, *, user_id: str, space_id: str) -> CommunityMembershipResponse:
        get_community_space(space_id)
        existing = self.memberships.get_membership(user_id=user_id, space_id=space_id)
        membership = existing or CommunityMembership(space_id=space_id, user_id=user_id)
        saved = self.memberships.save_membership(membership)
        emit_product_event(
            event_name="community_space_joined",
            module="community",
            surface="community",
            user_id=user_id,
            session_id=user_id,
            properties={"space_id": space_id},
        )
        return CommunityMembershipResponse(
            space_id=saved.space_id,
            role=saved.role,
            status=saved.status,
            joined_at=saved.joined_at,
        )


class ListCommunityPosts:
    def __init__(self, posts: CommunityPostRepository, comments: CommunityCommentRepository) -> None:
        self.posts = posts
        self.comments = comments

    def execute(self, *, space_id: str) -> list[CommunityPostResponse]:
        get_community_space(space_id)
        return [
            CommunityPostResponse(
                post_id=item.post_id,
                space_id=item.space_id,
                user_id=item.user_id,
                post_type=item.post_type,
                title=item.title,
                body=item.body,
                moderation_status=item.moderation_status,
                created_at=item.created_at,
                updated_at=item.updated_at,
                comments=_build_comment_tree(self.comments.list_comments(post_id=item.post_id)),
            )
            for item in self.posts.list_posts(space_id=space_id)
        ]


class CreateCommunityPost:
    def __init__(
        self,
        memberships: CommunityMembershipRepository,
        posts: CommunityPostRepository,
        moderation: CommunityModerationRepository,
    ) -> None:
        self.memberships = memberships
        self.posts = posts
        self.moderation = moderation

    def execute(
        self,
        *,
        user_id: str,
        space_id: str,
        post_type: str,
        title: str,
        body: str,
        linked_lesson_id: str | None,
        linked_goal_id: str | None,
        linked_case_id: str | None,
    ) -> CommunityPostResponse:
        trust = TrustSafetyService()
        space = get_community_space(space_id)
        membership = self.memberships.get_membership(user_id=user_id, space_id=space_id)
        if membership is None:
            raise ValueError("Bạn cần tham gia space trước khi đăng bài.")

        decision = moderate_post(
            title=title,
            body=body,
            space_type=space.space_type,
            recent_post_count=self.posts.count_recent_posts(user_id=user_id, minutes=10),
        )
        trust_review = trust.analyze_text(surface="community", text=f"{title}\n{body}")
        final_status = decision.decision
        if trust_review.action == "block":
            final_status = "blocked"
        elif trust_review.action == "hold" and final_status == "published":
            final_status = "held_for_review"
        merged_labels = tuple(dict.fromkeys([*decision.labels, *trust_review.risk_classes]))
        explanation = trust_review.explanation if trust_review.action != "allow" else decision.explanation
        now = utc_now_iso()
        post = CommunityPost(
            post_id=new_community_post_id(),
            space_id=space_id,
            user_id=user_id,
            post_type=post_type,
            title=title.strip(),
            body=body.strip(),
            linked_lesson_id=linked_lesson_id,
            linked_goal_id=linked_goal_id,
            linked_case_id=linked_case_id,
            moderation_status=final_status,
            created_at=now,
            updated_at=now,
        )
        self.posts.save_post(post)
        self.moderation.save_event(
            CommunityModerationEvent(
                event_id=new_community_event_id(),
                content_type="post",
                content_id=post.post_id,
                user_id=user_id,
                ai_risk_labels=merged_labels,
                decision=final_status,
                notes=explanation,
            )
        )
        trust.record_audit(
            actor_id=user_id,
            surface="community",
            topic=space.space_type,
            channel="community_post",
            risk_classes=merged_labels,
            route_decision=final_status,
            input_summary=title,
            output_summary=post.body[:180],
            escalation_action=trust_review.action if trust_review.action != "allow" else None,
        )
        emit_product_event(
            event_name="community_post_created" if final_status == "published" else (
                "community_post_held_for_review" if final_status == "held_for_review" else "community_post_blocked"
            ),
            module="community",
            surface="community",
            user_id=user_id,
            session_id=user_id,
            properties={"space_id": space_id, "moderation_status": final_status, "risk_labels": list(merged_labels)},
        )
        return CommunityPostResponse(
            post_id=post.post_id,
            space_id=post.space_id,
            user_id=post.user_id,
            post_type=post.post_type,
            title=post.title,
            body=post.body,
            moderation_status=post.moderation_status,
            moderation_labels=list(merged_labels),
            moderation_message=explanation,
            created_at=post.created_at,
            updated_at=post.updated_at,
        )


class CreateCommunityComment:
    def __init__(
        self,
        memberships: CommunityMembershipRepository,
        posts: CommunityPostRepository,
        comments: CommunityCommentRepository,
        moderation: CommunityModerationRepository,
    ) -> None:
        self.memberships = memberships
        self.posts = posts
        self.comments = comments
        self.moderation = moderation

    def execute(
        self,
        *,
        user_id: str,
        post_id: str,
        body: str,
        parent_comment_id: str | None = None,
    ) -> CommunityCommentResponse:
        trust = TrustSafetyService()
        post = self.posts.get_post(post_id=post_id)
        if post is None:
            raise ValueError("Không tìm thấy post để comment.")
        membership = self.memberships.get_membership(user_id=user_id, space_id=post.space_id)
        if membership is None:
            raise ValueError("Bạn cần tham gia space trước khi bình luận.")
        parent_comment = None
        thread_depth = 0
        if parent_comment_id:
            parent_comment = self.comments.get_comment(comment_id=parent_comment_id)
            if parent_comment is None or parent_comment.post_id != post_id:
                raise ValueError("Reply không hợp lệ cho post này.")
            if parent_comment.thread_depth >= 2:
                raise ValueError("Thread depth toi da la 3 tang de giu discussion de doc.")
            thread_depth = parent_comment.thread_depth + 1

        decision = moderate_post(
            title=f"comment:{post.title}",
            body=body,
            space_type=get_community_space(post.space_id).space_type,
            recent_post_count=self.posts.count_recent_posts(user_id=user_id, minutes=10),
        )
        trust_review = trust.analyze_text(surface="community", text=body)
        final_status = decision.decision
        if trust_review.action == "block":
            final_status = "blocked"
        elif trust_review.action == "hold" and final_status == "published":
            final_status = "held_for_review"
        merged_labels = tuple(dict.fromkeys([*decision.labels, *trust_review.risk_classes]))
        explanation = trust_review.explanation if trust_review.action != "allow" else decision.explanation
        now = utc_now_iso()
        comment = CommunityComment(
            comment_id=new_community_comment_id(),
            post_id=post_id,
            user_id=user_id,
            parent_comment_id=parent_comment.comment_id if parent_comment is not None else None,
            thread_depth=thread_depth,
            body=body.strip(),
            moderation_status=final_status,
            created_at=now,
            updated_at=now,
        )
        self.comments.save_comment(comment)
        self.moderation.save_event(
            CommunityModerationEvent(
                event_id=new_community_event_id(),
                content_type="comment",
                content_id=comment.comment_id,
                user_id=user_id,
                ai_risk_labels=merged_labels,
                decision=final_status,
                notes=explanation,
            )
        )
        trust.record_audit(
            actor_id=user_id,
            surface="community",
            topic="comment",
            channel="community_comment",
            risk_classes=merged_labels,
            route_decision=final_status,
            input_summary=body,
            output_summary=comment.body[:180],
            escalation_action=trust_review.action if trust_review.action != "allow" else None,
        )
        emit_product_event(
            event_name="community_reply_created" if parent_comment_id else "community_comment_created",
            module="community",
            surface="community",
            user_id=user_id,
            session_id=user_id,
            properties={
                "post_id": post_id,
                "moderation_status": final_status,
                "parent_comment_id": parent_comment_id,
            },
        )
        return CommunityCommentResponse(
            comment_id=comment.comment_id,
            post_id=comment.post_id,
            user_id=comment.user_id,
            body=comment.body,
            parent_comment_id=comment.parent_comment_id,
            thread_depth=comment.thread_depth,
            moderation_status=comment.moderation_status,
            moderation_labels=list(merged_labels),
            moderation_message=explanation,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )


class ListCommunityModerationQueue:
    def __init__(
        self,
        moderation: CommunityModerationRepository,
        posts: CommunityPostRepository,
        comments: CommunityCommentRepository,
    ) -> None:
        self.moderation = moderation
        self.posts = posts
        self.comments = comments

    def execute(
        self,
        *,
        space_id: str | None = None,
        risk_label: str | None = None,
        search: str | None = None,
    ) -> list[CommunityModerationQueueItemResponse]:
        items: list[CommunityModerationQueueItemResponse] = []
        for event in self.moderation.list_pending_queue():
            if event.content_type == "post":
                post = self.posts.get_post(post_id=event.content_id)
                if post is None or post.moderation_status != "held_for_review":
                    continue
                items.append(
                    CommunityModerationQueueItemResponse(
                        event_id=event.event_id,
                        content_type=event.content_type,
                        content_id=event.content_id,
                        user_id=event.user_id,
                        decision=event.decision,
                        ai_risk_labels=list(event.ai_risk_labels),
                        notes=event.notes,
                        created_at=event.created_at,
                        content_preview=f"{post.title}\n{post.body[:240]}",
                        space_id=post.space_id,
                    )
                )
                continue
            comment = self.comments.get_comment(comment_id=event.content_id)
            if comment is None or comment.moderation_status != "held_for_review":
                continue
            parent = self.posts.get_post(post_id=comment.post_id)
            items.append(
                CommunityModerationQueueItemResponse(
                    event_id=event.event_id,
                    content_type=event.content_type,
                    content_id=event.content_id,
                    user_id=event.user_id,
                    decision=event.decision,
                    ai_risk_labels=list(event.ai_risk_labels),
                    notes=event.notes,
                    created_at=event.created_at,
                    content_preview=comment.body[:240],
                    space_id=parent.space_id if parent is not None else None,
                )
                )
        search_value = search.strip().lower() if search else None
        filtered = items
        if space_id:
            filtered = [item for item in filtered if item.space_id == space_id]
        if risk_label:
            filtered = [item for item in filtered if risk_label in item.ai_risk_labels]
        if search_value:
            filtered = [
                item
                for item in filtered
                if search_value in item.content_preview.lower() or search_value in (item.space_id or "").lower()
            ]
        return filtered


class ReviewCommunityModerationItem:
    def __init__(
        self,
        moderation: CommunityModerationRepository,
        posts: CommunityPostRepository,
        comments: CommunityCommentRepository,
    ) -> None:
        self.moderation = moderation
        self.posts = posts
        self.comments = comments

    def execute(
        self,
        *,
        content_type: str,
        content_id: str,
        action: str,
        reviewer_id: str,
        notes: str | None,
    ) -> CommunityModerationQueueItemResponse:
        final_status = "published" if action == "publish" else "rejected"
        if content_type == "post":
            post = self.posts.get_post(post_id=content_id)
            if post is None:
                raise ValueError("Không tìm thấy post trong moderation queue.")
            self.posts.update_post_status(post_id=content_id, moderation_status=final_status)
            self.moderation.save_event(
                CommunityModerationEvent(
                    event_id=new_community_event_id(),
                    content_type="post",
                    content_id=content_id,
                    user_id=post.user_id,
                    ai_risk_labels=(),
                    decision=final_status,
                    reviewer_id=reviewer_id,
                    notes=notes or f"Moderator quyết định {final_status}.",
                )
            )
            return CommunityModerationQueueItemResponse(
                event_id="reviewed",
                content_type="post",
                content_id=content_id,
                user_id=post.user_id,
                decision=final_status,
                ai_risk_labels=[],
                notes=notes,
                created_at=utc_now_iso(),
                content_preview=f"{post.title}\n{post.body[:240]}",
                space_id=post.space_id,
            )

        comment = self.comments.get_comment(comment_id=content_id)
        if comment is None:
            raise ValueError("Không tìm thấy comment trong moderation queue.")
        self.comments.update_comment_status(comment_id=content_id, moderation_status=final_status)
        self.moderation.save_event(
            CommunityModerationEvent(
                event_id=new_community_event_id(),
                content_type="comment",
                content_id=content_id,
                user_id=comment.user_id,
                ai_risk_labels=(),
                decision=final_status,
                reviewer_id=reviewer_id,
                notes=notes or f"Moderator quyết định {final_status}.",
            )
        )
        parent = self.posts.get_post(post_id=comment.post_id)
        return CommunityModerationQueueItemResponse(
            event_id="reviewed",
            content_type="comment",
            content_id=content_id,
            user_id=comment.user_id,
            decision=final_status,
            ai_risk_labels=[],
            notes=notes,
            created_at=utc_now_iso(),
            content_preview=comment.body[:240],
            space_id=parent.space_id if parent is not None else None,
        )


class UpdateCommunityNotificationState:
    def __init__(self, notifications: CommunityNotificationRepository) -> None:
        self.notifications = notifications

    def execute(self, *, notification_id: str, action: str) -> CommunityNotificationResponse:
        target_status = "read" if action == "read" else "dismissed"
        notification = self.notifications.update_status(notification_id=notification_id, status=target_status)
        if notification is None:
            raise ValueError("Không tìm thấy community notification.")
        return CommunityNotificationResponse(
            notification_id=notification.notification_id,
            notification_type=notification.notification_type,
            title=notification.title,
            message=notification.message,
            cta_path=notification.cta_path,
            related_space_id=notification.related_space_id,
            status=notification.status,
            created_at=notification.created_at,
            updated_at=notification.updated_at,
            next_reminder_at=notification.next_reminder_at,
        )


def _sync_challenge_progress(
    *,
    user_id: str,
    memberships: list[CommunityMembership],
    posts: CommunityPostRepository,
    challenges: CommunityChallengeProgressRepository,
    completed_lessons: int,
    goal_count: int,
) -> list[CommunityChallengeProgress]:
    joined_ids = {item.space_id for item in memberships}
    definitions = [space for space in list_community_spaces() if space.space_type == "guided_challenge"]
    results: list[CommunityChallengeProgress] = []
    for space in definitions:
        previous = challenges.get_progress(challenge_id=space.space_id, user_id=user_id)
        published_posts = posts.count_posts_by_status_for_space(
            user_id=user_id,
            space_id=space.space_id,
            status="published",
        )
        progress_pct = 0
        if goal_count > 0:
            progress_pct += 40
        if space.space_id in joined_ids:
            progress_pct += 25
        if completed_lessons > 0:
            progress_pct += 20
        if published_posts > 0:
            progress_pct += 15
        progress_pct = min(progress_pct, 100)
        status = "not_started"
        if progress_pct >= 100:
            status = "completed"
        elif progress_pct > 0:
            status = "in_progress"
        last_active_at = (
            previous.last_active_at
            if previous is not None and previous.progress_pct == progress_pct and previous.status == status
            else utc_now_iso()
        )
        progress = CommunityChallengeProgress(
            challenge_id=space.space_id,
            user_id=user_id,
            status=status,
            progress_pct=progress_pct,
            last_active_at=last_active_at,
        )
        challenges.save_progress(progress)
        results.append(progress)
    return results


def _sync_notifications(
    *,
    user_id: str,
    memberships: list[CommunityMembership],
    challenge_progress: list[CommunityChallengeProgress],
    recommended_ids: list[str],
    goal_count: int,
    existing_notifications: list[CommunityNotificationState],
) -> list[CommunityNotificationState]:
    joined_ids = {item.space_id for item in memberships}
    now = utc_now_iso()
    now_dt = datetime.now(timezone.utc)
    existing_map = {item.notification_id: item for item in existing_notifications}
    notifications: list[CommunityNotificationState] = []

    in_progress = next((item for item in challenge_progress if item.status == "in_progress"), None)
    if in_progress is not None:
        notification_id = f"cnotif_{user_id}_{in_progress.challenge_id}_progress"
        notifications.append(
            _merge_notification(
                existing=existing_map.get(notification_id),
                notification=CommunityNotificationState(
                    notification_id=notification_id,
                    user_id=user_id,
                    notification_type="challenge_progress",
                    title="Challenge đang dang dở cần một lần check-in nữa",
                    message=(
                        f"Challenge {in_progress.challenge_id} đang ở {in_progress.progress_pct}%. "
                        "Quay lại một lần ngắn để giữ nhịp học và cập nhật tiến độ."
                    ),
                    cta_path=f"/community?space={in_progress.challenge_id}",
                    related_space_id=in_progress.challenge_id,
                    status="active",
                    created_at=now,
                    updated_at=now,
                    next_reminder_at=_cadence_from_last_active(
                        last_active_at=in_progress.last_active_at,
                        frequency_days=3 if in_progress.progress_pct < 50 else 5,
                    ),
                ),
                now_dt=now_dt,
            )
        )

    if goal_count > 0 and "goal-checkin-challenge" not in joined_ids:
        notification_id = f"cnotif_{user_id}_goal_checkin_join"
        notifications.append(
            _merge_notification(
                existing=existing_map.get(notification_id),
                notification=CommunityNotificationState(
                    notification_id=notification_id,
                    user_id=user_id,
                    notification_type="join_challenge",
                    title="Bạn đã có goal, đây là lúc tham gia challenge check-in",
                    message="Challenge 14 ngày giúp bạn quay lại app đều hơn mà không bị quá tải.",
                    cta_path="/community?space=goal-checkin-challenge",
                    related_space_id="goal-checkin-challenge",
                    status="active",
                    created_at=now,
                    updated_at=now,
                    next_reminder_at=(now_dt + timedelta(days=2)).isoformat(),
                ),
                now_dt=now_dt,
            )
        )

    recommended_unjoined = next((space_id for space_id in recommended_ids if space_id not in joined_ids), None)
    if recommended_unjoined is not None:
        space = get_community_space(recommended_unjoined)
        notification_id = f"cnotif_{user_id}_{recommended_unjoined}_join"
        notifications.append(
            _merge_notification(
                existing=existing_map.get(notification_id),
                notification=CommunityNotificationState(
                    notification_id=notification_id,
                    user_id=user_id,
                    notification_type="recommended_space",
                    title=f"Space tiếp theo phù hợp với bạn là {space.title}",
                    message=space.join_hint or "Tham gia space này để học cùng có kiểm soát.",
                    cta_path=f"/community?space={space.space_id}",
                    related_space_id=space.space_id,
                    status="active",
                    created_at=now,
                    updated_at=now,
                    next_reminder_at=(now_dt + timedelta(days=4)).isoformat(),
                ),
                now_dt=now_dt,
            )
        )

    return notifications[:3]


def _build_comment_tree(comments: list[CommunityComment]) -> list[CommunityCommentResponse]:
    nodes = {
        item.comment_id: CommunityCommentResponse(
            comment_id=item.comment_id,
            post_id=item.post_id,
            user_id=item.user_id,
            body=item.body,
            parent_comment_id=item.parent_comment_id,
            thread_depth=item.thread_depth,
            moderation_status=item.moderation_status,
            created_at=item.created_at,
            updated_at=item.updated_at,
            replies=[],
        )
        for item in comments
    }
    roots: list[CommunityCommentResponse] = []
    for item in comments:
        node = nodes[item.comment_id]
        if item.parent_comment_id and item.parent_comment_id in nodes:
            nodes[item.parent_comment_id].replies.append(node)
        else:
            roots.append(node)
    return roots


def _cadence_from_last_active(*, last_active_at: str, frequency_days: int) -> str:
    try:
        last_active = datetime.fromisoformat(last_active_at.replace("Z", "+00:00"))
    except ValueError:
        last_active = datetime.now(timezone.utc)
    return (last_active + timedelta(days=frequency_days)).isoformat()


def _merge_notification(
    *,
    existing: CommunityNotificationState | None,
    notification: CommunityNotificationState,
    now_dt: datetime,
) -> CommunityNotificationState:
    if existing is None:
        return notification

    created_at = existing.created_at
    updated_at = existing.updated_at
    status = existing.status
    next_due = notification.next_reminder_at
    due_reactivated = False
    if status == "dismissed":
        return CommunityNotificationState(
            notification_id=notification.notification_id,
            user_id=notification.user_id,
            notification_type=notification.notification_type,
            title=notification.title,
            message=notification.message,
            cta_path=notification.cta_path,
            related_space_id=notification.related_space_id,
            status="dismissed",
            created_at=created_at,
            updated_at=updated_at,
            next_reminder_at=next_due,
        )
    if status == "read" and next_due:
        due_dt = datetime.fromisoformat(next_due.replace("Z", "+00:00"))
        if now_dt >= due_dt:
            status = "active"
            updated_at = now_dt.isoformat()
            due_reactivated = True

    if status == "active" and not due_reactivated:
        updated_at = now_dt.isoformat()

    return CommunityNotificationState(
        notification_id=notification.notification_id,
        user_id=notification.user_id,
        notification_type=notification.notification_type,
        title=notification.title,
        message=notification.message,
        cta_path=notification.cta_path,
        related_space_id=notification.related_space_id,
        status=status,
        created_at=created_at,
        updated_at=updated_at,
        next_reminder_at=next_due,
    )


# ---------------------------------------------------------------------------
# Enriched dashboard helpers (demo/computed data for the redesigned frontend)
# ---------------------------------------------------------------------------

def _build_member_counts(memberships: list[CommunityMembership]) -> dict[str, int]:
    """Count members per space from real memberships, with demo base counts."""
    base: dict[str, int] = {
        "risk-literacy-circle": 9200,
        "goal-planning-circle": 7400,
        "goal-checkin-challenge": 3100,
        "company-case-room": 8900,
        "ask-an-expert-weekly": 12600,
        "diaspora-money-cohort": 3300,
    }
    for m in memberships:
        base[m.space_id] = base.get(m.space_id, 0) + 1
    return base


def _build_post_counts(posts: CommunityPostRepository) -> dict[str, int]:
    """Return demo post counts per space."""
    return {
        "risk-literacy-circle": 4700,
        "goal-planning-circle": 6200,
        "goal-checkin-challenge": 1800,
        "company-case-room": 8900,
        "ask-an-expert-weekly": 3300,
        "diaspora-money-cohort": 1200,
    }


def _build_community_stats() -> CommunityStatsResponse:
    return CommunityStatsResponse(
        active_members="36.2K",
        active_members_delta="↑ 8.2% so với tuần trước",
        discussions_today=482,
        discussions_delta="↑ 12.4% so với hôm qua",
        watchlists_shared="1.25K",
        watchlists_delta="↑ 9.3% so với tuần trước",
        questions_answered=318,
        questions_delta="↑ 10.4% so với hôm qua",
        moderation_status="Ổn định",
        moderation_note="0 cảnh báo mới hôm nay",
    )


def _build_top_contributors() -> list[CommunityTopContributorResponse]:
    return [
        CommunityTopContributorResponse(rank=1, user_id="user-mh", display_name="Minh Hoàng", role_badge="Pro Lab Member", points=12450),
        CommunityTopContributorResponse(rank=2, user_id="user-qh", display_name="Quang Huy", role_badge="Active Member", points=8230),
        CommunityTopContributorResponse(rank=3, user_id="user-tt", display_name="Thu Trang", role_badge="Active Member", points=6870),
        CommunityTopContributorResponse(rank=4, user_id="user-hn", display_name="Hoàng Nam", role_badge="Community Helper", points=5120),
    ]


def _build_trending_topics() -> list[CommunityTrendingTopicResponse]:
    return [
        CommunityTrendingTopicResponse(topic_id="bctc", label="BCTC", post_count="2.1K"),
        CommunityTrendingTopicResponse(topic_id="risk-management", label="Risk Management", post_count="1.8K"),
        CommunityTrendingTopicResponse(topic_id="goal-planning", label="Goal Planning", post_count="1.5K"),
        CommunityTrendingTopicResponse(topic_id="watchlist", label="Watchlist", post_count="1.2K"),
        CommunityTrendingTopicResponse(topic_id="macro", label="Macro", post_count="980"),
        CommunityTrendingTopicResponse(topic_id="learning-path", label="Learning Path", post_count="870"),
    ]


def _build_community_events() -> list[CommunityEventResponse]:
    return [
        CommunityEventResponse(event_id="evt-1", title="Weekly Market Brief", schedule="Thứ 3, 20/05 · 20:00", cta_label="Tham gia"),
        CommunityEventResponse(event_id="evt-2", title="Ask Me Anything (AMA)", schedule="Thứ 4, 22/05 · 20:00", cta_label="Tham gia"),
        CommunityEventResponse(event_id="evt-3", title="BCTC Study Group", schedule="Thứ 7, 25/05 · 10:00", cta_label="Tham gia"),
    ]


def _build_saved_discussions() -> list[CommunitySavedDiscussionResponse]:
    return [
        CommunitySavedDiscussionResponse(discussion_id="sd-1", title="Đọc tín ETF & tài liệu đọng đến VN-Index", snippet="4 bình luận · 12 lượt thích"),
        CommunitySavedDiscussionResponse(discussion_id="sd-2", title="Checklist phân tích BCTC nhanh", snippet="8 bình luận · 23 lượt thích"),
        CommunitySavedDiscussionResponse(discussion_id="sd-3", title="Quản trị cá nhân khi thị trường biến động", snippet="6 bình luận · 15 lượt thích"),
    ]

