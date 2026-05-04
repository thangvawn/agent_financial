from __future__ import annotations

import json
import uuid

from risk_dashboard.modules.community.domain.entities import (
    CommunityChallengeProgress,
    CommunityComment,
    CommunityMembership,
    CommunityModerationEvent,
    CommunityNotificationState,
    CommunityPost,
)
from risk_dashboard.modules.community.domain.ports import (
    CommunityChallengeProgressRepository,
    CommunityCommentRepository,
    CommunityMembershipRepository,
    CommunityModerationRepository,
    CommunityNotificationRepository,
    CommunityPostRepository,
)
from risk_dashboard.platform.database import open_app_state_db, reset_app_state_tables


def new_community_post_id() -> str:
    return f"cpost_{uuid.uuid4().hex[:12]}"


def new_community_event_id() -> str:
    return f"cevt_{uuid.uuid4().hex[:12]}"


def new_community_comment_id() -> str:
    return f"ccmt_{uuid.uuid4().hex[:12]}"


def new_community_notification_id() -> str:
    return f"cnotif_{uuid.uuid4().hex[:12]}"


class SqliteCommunityMembershipRepository(CommunityMembershipRepository):
    def list_memberships(self, *, user_id: str) -> list[CommunityMembership]:
        with open_app_state_db() as conn:
            rows = conn.execute(
                """
                SELECT space_id, user_id, role, joined_at, status
                FROM community_memberships
                WHERE user_id = ?
                ORDER BY joined_at DESC
                """,
                (user_id,),
            ).fetchall()
        return [
            CommunityMembership(
                space_id=row["space_id"],
                user_id=row["user_id"],
                role=row["role"],
                joined_at=row["joined_at"],
                status=row["status"],
            )
            for row in rows
        ]

    def get_membership(self, *, user_id: str, space_id: str) -> CommunityMembership | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT space_id, user_id, role, joined_at, status
                FROM community_memberships
                WHERE user_id = ? AND space_id = ?
                """,
                (user_id, space_id),
            ).fetchone()
        if row is None:
            return None
        return CommunityMembership(
            space_id=row["space_id"],
            user_id=row["user_id"],
            role=row["role"],
            joined_at=row["joined_at"],
            status=row["status"],
        )

    def save_membership(self, membership: CommunityMembership) -> CommunityMembership:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO community_memberships (space_id, user_id, role, joined_at, status)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(space_id, user_id) DO UPDATE SET
                  role = excluded.role,
                  joined_at = excluded.joined_at,
                  status = excluded.status
                """,
                (
                    membership.space_id,
                    membership.user_id,
                    membership.role,
                    membership.joined_at,
                    membership.status,
                ),
            )
            conn.commit()
        return membership


class SqliteCommunityPostRepository(CommunityPostRepository):
    def list_posts(self, *, space_id: str, visible_only: bool = True) -> list[CommunityPost]:
        with open_app_state_db() as conn:
            query = """
                SELECT post_id, space_id, user_id, post_type, title, body, linked_lesson_id, linked_goal_id,
                       linked_case_id, moderation_status, created_at, updated_at
                FROM community_posts
                WHERE space_id = ?
            """
            params: tuple[object, ...]
            if visible_only:
                query += " AND moderation_status = 'published'"
                params = (space_id,)
            else:
                params = (space_id,)
            query += " ORDER BY created_at DESC"
            rows = conn.execute(query, params).fetchall()
        return [
            CommunityPost(
                post_id=row["post_id"],
                space_id=row["space_id"],
                user_id=row["user_id"],
                post_type=row["post_type"],
                title=row["title"],
                body=row["body"],
                linked_lesson_id=row["linked_lesson_id"],
                linked_goal_id=row["linked_goal_id"],
                linked_case_id=row["linked_case_id"],
                moderation_status=row["moderation_status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def get_post(self, *, post_id: str) -> CommunityPost | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT post_id, space_id, user_id, post_type, title, body, linked_lesson_id, linked_goal_id,
                       linked_case_id, moderation_status, created_at, updated_at
                FROM community_posts
                WHERE post_id = ?
                """,
                (post_id,),
            ).fetchone()
        if row is None:
            return None
        return CommunityPost(
            post_id=row["post_id"],
            space_id=row["space_id"],
            user_id=row["user_id"],
            post_type=row["post_type"],
            title=row["title"],
            body=row["body"],
            linked_lesson_id=row["linked_lesson_id"],
            linked_goal_id=row["linked_goal_id"],
            linked_case_id=row["linked_case_id"],
            moderation_status=row["moderation_status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def save_post(self, post: CommunityPost) -> CommunityPost:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO community_posts (
                  post_id, space_id, user_id, post_type, title, body, linked_lesson_id, linked_goal_id,
                  linked_case_id, moderation_status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(post_id) DO UPDATE SET
                  title = excluded.title,
                  body = excluded.body,
                  linked_lesson_id = excluded.linked_lesson_id,
                  linked_goal_id = excluded.linked_goal_id,
                  linked_case_id = excluded.linked_case_id,
                  moderation_status = excluded.moderation_status,
                  updated_at = excluded.updated_at
                """,
                (
                    post.post_id,
                    post.space_id,
                    post.user_id,
                    post.post_type,
                    post.title,
                    post.body,
                    post.linked_lesson_id,
                    post.linked_goal_id,
                    post.linked_case_id,
                    post.moderation_status,
                    post.created_at,
                    post.updated_at,
                ),
            )
            conn.commit()
        return post

    def update_post_status(self, *, post_id: str, moderation_status: str) -> None:
        with open_app_state_db() as conn:
            conn.execute(
                "UPDATE community_posts SET moderation_status = ?, updated_at = datetime('now') WHERE post_id = ?",
                (moderation_status, post_id),
            )
            conn.commit()

    def count_recent_posts(self, *, user_id: str, minutes: int) -> int:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM community_posts
                WHERE user_id = ?
                  AND datetime(created_at) >= datetime('now', ?)
                """,
                (user_id, f"-{minutes} minutes"),
            ).fetchone()
        return int(row["count"] or 0)

    def count_posts_by_status(self, *, user_id: str, status: str) -> int:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM community_posts
                WHERE user_id = ? AND moderation_status = ?
                """,
                (user_id, status),
            ).fetchone()
        return int(row["count"] or 0)

    def count_posts_by_status_for_space(self, *, user_id: str, space_id: str, status: str) -> int:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM community_posts
                WHERE user_id = ? AND space_id = ? AND moderation_status = ?
                """,
                (user_id, space_id, status),
            ).fetchone()
        return int(row["count"] or 0)


class SqliteCommunityCommentRepository(CommunityCommentRepository):
    def list_comments(self, *, post_id: str, visible_only: bool = True) -> list[CommunityComment]:
        with open_app_state_db() as conn:
            query = """
                SELECT comment_id, post_id, user_id, parent_comment_id, thread_depth, body, moderation_status, created_at,
                       COALESCE(updated_at, created_at) AS updated_at
                FROM community_comments
                WHERE post_id = ?
            """
            params: tuple[object, ...]
            if visible_only:
                query += " AND moderation_status = 'published'"
                params = (post_id,)
            else:
                params = (post_id,)
            query += " ORDER BY created_at ASC"
            rows = conn.execute(query, params).fetchall()
        return [
            CommunityComment(
                comment_id=row["comment_id"],
                post_id=row["post_id"],
                user_id=row["user_id"],
                parent_comment_id=row["parent_comment_id"],
                thread_depth=int(row["thread_depth"] or 0),
                body=row["body"],
                moderation_status=row["moderation_status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def get_comment(self, *, comment_id: str) -> CommunityComment | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT comment_id, post_id, user_id, parent_comment_id, thread_depth, body, moderation_status, created_at,
                       COALESCE(updated_at, created_at) AS updated_at
                FROM community_comments
                WHERE comment_id = ?
                """,
                (comment_id,),
            ).fetchone()
        if row is None:
            return None
        return CommunityComment(
            comment_id=row["comment_id"],
            post_id=row["post_id"],
            user_id=row["user_id"],
            parent_comment_id=row["parent_comment_id"],
            thread_depth=int(row["thread_depth"] or 0),
            body=row["body"],
            moderation_status=row["moderation_status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def save_comment(self, comment: CommunityComment) -> CommunityComment:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO community_comments (
                  comment_id, post_id, user_id, parent_comment_id, thread_depth, body, moderation_status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(comment_id) DO UPDATE SET
                  parent_comment_id = excluded.parent_comment_id,
                  thread_depth = excluded.thread_depth,
                  body = excluded.body,
                  moderation_status = excluded.moderation_status,
                  updated_at = excluded.updated_at
                """,
                (
                    comment.comment_id,
                    comment.post_id,
                    comment.user_id,
                    comment.parent_comment_id,
                    comment.thread_depth,
                    comment.body,
                    comment.moderation_status,
                    comment.created_at,
                    comment.updated_at,
                ),
            )
            conn.commit()
        return comment

    def update_comment_status(self, *, comment_id: str, moderation_status: str) -> None:
        with open_app_state_db() as conn:
            conn.execute(
                "UPDATE community_comments SET moderation_status = ?, updated_at = datetime('now') WHERE comment_id = ?",
                (moderation_status, comment_id),
            )
            conn.commit()


class SqliteCommunityModerationRepository(CommunityModerationRepository):
    def save_event(self, event: CommunityModerationEvent) -> CommunityModerationEvent:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO community_moderation_events (
                  event_id, content_type, content_id, user_id, ai_risk_labels_json, decision, reviewer_id, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.content_type,
                    event.content_id,
                    event.user_id,
                    json.dumps(list(event.ai_risk_labels), ensure_ascii=False),
                    event.decision,
                    event.reviewer_id,
                    event.notes,
                    event.created_at,
                ),
            )
            conn.commit()
        return event

    def list_pending_queue(self) -> list[CommunityModerationEvent]:
        with open_app_state_db() as conn:
            rows = conn.execute(
                """
                SELECT event_id, content_type, content_id, user_id, ai_risk_labels_json, decision, reviewer_id, notes, created_at
                FROM community_moderation_events
                WHERE decision = 'held_for_review'
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [
            CommunityModerationEvent(
                event_id=row["event_id"],
                content_type=row["content_type"],
                content_id=row["content_id"],
                user_id=row["user_id"],
                ai_risk_labels=tuple(json.loads(row["ai_risk_labels_json"] or "[]")),
                decision=row["decision"],
                reviewer_id=row["reviewer_id"],
                notes=row["notes"],
                created_at=row["created_at"],
            )
            for row in rows
        ]


class SqliteCommunityChallengeProgressRepository(CommunityChallengeProgressRepository):
    def get_progress(self, *, challenge_id: str, user_id: str) -> CommunityChallengeProgress | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT challenge_id, user_id, status, progress_pct, last_active_at
                FROM community_challenge_progress
                WHERE challenge_id = ? AND user_id = ?
                """,
                (challenge_id, user_id),
            ).fetchone()
        if row is None:
            return None
        return CommunityChallengeProgress(
            challenge_id=row["challenge_id"],
            user_id=row["user_id"],
            status=row["status"],
            progress_pct=row["progress_pct"],
            last_active_at=row["last_active_at"],
        )

    def list_progress(self, *, user_id: str) -> list[CommunityChallengeProgress]:
        with open_app_state_db() as conn:
            rows = conn.execute(
                """
                SELECT challenge_id, user_id, status, progress_pct, last_active_at
                FROM community_challenge_progress
                WHERE user_id = ?
                ORDER BY last_active_at DESC
                """,
                (user_id,),
            ).fetchall()
        return [
            CommunityChallengeProgress(
                challenge_id=row["challenge_id"],
                user_id=row["user_id"],
                status=row["status"],
                progress_pct=row["progress_pct"],
                last_active_at=row["last_active_at"],
            )
            for row in rows
        ]

    def save_progress(self, progress: CommunityChallengeProgress) -> CommunityChallengeProgress:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO community_challenge_progress (challenge_id, user_id, status, progress_pct, last_active_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(challenge_id, user_id) DO UPDATE SET
                  status = excluded.status,
                  progress_pct = excluded.progress_pct,
                  last_active_at = excluded.last_active_at
                """,
                (
                    progress.challenge_id,
                    progress.user_id,
                    progress.status,
                    progress.progress_pct,
                    progress.last_active_at,
                ),
            )
            conn.commit()
        return progress


class SqliteCommunityNotificationRepository(CommunityNotificationRepository):
    def list_notifications(self, *, user_id: str, active_only: bool = True) -> list[CommunityNotificationState]:
        with open_app_state_db() as conn:
            query = """
                SELECT notification_id, user_id, notification_type, title, message, cta_path,
                       related_space_id, status, created_at, updated_at, next_reminder_at
                FROM community_notification_states
                WHERE user_id = ?
            """
            params: tuple[object, ...] = (user_id,)
            if active_only:
                query += " AND status = 'active'"
            query += " ORDER BY updated_at DESC, created_at DESC"
            rows = conn.execute(query, params).fetchall()
        return [
            CommunityNotificationState(
                notification_id=row["notification_id"],
                user_id=row["user_id"],
                notification_type=row["notification_type"],
                title=row["title"],
                message=row["message"],
                cta_path=row["cta_path"],
                related_space_id=row["related_space_id"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                next_reminder_at=row["next_reminder_at"],
            )
            for row in rows
        ]

    def replace_notifications(self, *, user_id: str, notifications: list[CommunityNotificationState]) -> None:
        with open_app_state_db() as conn:
            conn.execute("DELETE FROM community_notification_states WHERE user_id = ?", (user_id,))
            for item in notifications:
                conn.execute(
                    """
                    INSERT INTO community_notification_states (
                      notification_id, user_id, notification_type, title, message, cta_path,
                      related_space_id, status, created_at, updated_at, next_reminder_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.notification_id,
                        item.user_id,
                        item.notification_type,
                        item.title,
                        item.message,
                        item.cta_path,
                        item.related_space_id,
                        item.status,
                        item.created_at,
                        item.updated_at,
                        item.next_reminder_at,
                    ),
                )
            conn.commit()

    def update_status(self, *, notification_id: str, status: str) -> CommunityNotificationState | None:
        with open_app_state_db() as conn:
            conn.execute(
                """
                UPDATE community_notification_states
                SET status = ?, updated_at = datetime('now')
                WHERE notification_id = ?
                """,
                (status, notification_id),
            )
            row = conn.execute(
                """
                SELECT notification_id, user_id, notification_type, title, message, cta_path,
                       related_space_id, status, created_at, updated_at, next_reminder_at
                FROM community_notification_states
                WHERE notification_id = ?
                """,
                (notification_id,),
            ).fetchone()
            conn.commit()
        if row is None:
            return None
        return CommunityNotificationState(
            notification_id=row["notification_id"],
            user_id=row["user_id"],
            notification_type=row["notification_type"],
            title=row["title"],
            message=row["message"],
            cta_path=row["cta_path"],
            related_space_id=row["related_space_id"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            next_reminder_at=row["next_reminder_at"],
        )


def reset_community_state() -> None:
    reset_app_state_tables()
