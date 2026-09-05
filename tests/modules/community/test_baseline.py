"""Baseline regression tests for legacy community module.
Captures current behavior WITHOUT HTTP (router unmounted).
Serves as behavioral contract that must not regress before reactivation.
"""
from __future__ import annotations

import pytest

from risk_dashboard.modules.community.domain.entities import (
    CommunityComment,
    CommunityMembership,
    CommunityModerationDecision,
    CommunityNotificationState,
    CommunityPost,
    CommunityReputation,
    CommunitySpace,
)
from risk_dashboard.modules.community.domain.policies import (
    BLOCK_PATTERNS,
    HOLD_PATTERNS,
    build_reputation,
    moderate_post,
    recommend_space_ids,
)
from risk_dashboard.modules.community.schemas.requests import (
    CommunityCommentCreateRequest,
    CommunityJoinRequest,
    CommunityModerationReviewRequest,
    CommunityNotificationStateRequest,
    CommunityPostCreateRequest,
)
from risk_dashboard.modules.community.schemas.responses import (
    CommunityMembershipResponse,
    CommunityModerationQueueItemResponse,
    CommunityPostResponse,
    CommunityReputationResponse,
    CommunitySpaceResponse,
)


class TestCommunityBaseline:
    def test_moderate_post_published_when_clean(self) -> None:
        decision = moderate_post(
            title="Hỏi về cách tính ROE trong BCTC",
            body="Mình đang đọc bài phân tích tài chính và muốn hiểu rõ ROE phản ánh điều gì.",
            space_type="discussion",
            recent_post_count=0,
        )
        assert decision.decision == "published"
        assert decision.escalation_level == 0
        assert len(decision.labels) == 0

    def test_moderate_post_blocked_pump_and_dump(self) -> None:
        decision = moderate_post(
            title="Kèo này mua ngay all in x3 tài khoản",
            body="Vào lệnh ngay ngày mai không là lỡ tàu ăn bằng lần nhé.",
            space_type="discussion",
            recent_post_count=0,
        )
        assert decision.decision == "blocked"
        assert "pump_and_dump" in decision.labels
        assert decision.escalation_level == 3

    def test_moderate_post_blocked_off_platform_lure(self) -> None:
        decision = moderate_post(
            title="Vào room riêng để nhận phím hàng",
            body="Mọi người add zalo hoặc vào nhóm telegram link nhóm ở bio nhé.",
            space_type="discussion",
            recent_post_count=0,
        )
        assert decision.decision == "blocked"
        assert "off_platform_lure" in decision.labels
        assert decision.escalation_level == 3

    def test_moderate_post_held_direct_advice(self) -> None:
        decision = moderate_post(
            title="Nên mua mã nào phiên mai?",
            body="Mọi người cho mình xin giá mục tiêu của mã FPT với ạ.",
            space_type="discussion",
            recent_post_count=0,
        )
        assert decision.decision == "held_for_review"
        assert "direct_advice" in decision.labels
        assert decision.escalation_level == 2

    def test_moderate_post_held_certainty_claim(self) -> None:
        decision = moderate_post(
            title="Thị trường phiên tới chắc tăng",
            body="Kèo này bao lời chắc ăn 100% không thể giảm.",
            space_type="discussion",
            recent_post_count=0,
        )
        assert decision.decision == "held_for_review"
        assert "certainty_claim" in decision.labels

    def test_moderate_post_held_rate_limit(self) -> None:
        decision = moderate_post(
            title="Câu hỏi thảo luận số 4",
            body="Nội dung thảo luận hoàn toàn bình thường và mang tính học tập.",
            space_type="discussion",
            recent_post_count=3,
        )
        assert decision.decision == "held_for_review"
        assert "rate_limit_review" in decision.labels

    def test_moderate_post_ask_expert_queue(self) -> None:
        decision = moderate_post(
            title="Hỏi chuyên gia về định giá DCF",
            body="Làm sao để ước tính tỷ lệ chiết khấu WACC chuẩn xác cho doanh nghiệp nhỏ?",
            space_type="ask_expert",
            recent_post_count=0,
        )
        assert decision.decision == "held_for_review"
        assert "expert_queue" in decision.labels

    def test_build_reputation_tiers(self) -> None:
        # Learner tier
        rep_low = build_reputation(
            user_id="user-001",
            completed_lessons=1,
            goal_count=0,
            published_posts=1,
            held_posts=0,
            blocked_posts=0,
        )
        assert rep_low.reputation_band == "learner"
        assert rep_low.moderation_strike_count == 0

        # Consistent learner tier
        rep_mid = build_reputation(
            user_id="user-002",
            completed_lessons=3,
            goal_count=1,
            published_posts=2,
            held_posts=0,
            blocked_posts=0,
        )
        assert rep_mid.reputation_band == "consistent_learner"

        # Helpful contributor tier
        rep_high = build_reputation(
            user_id="user-003",
            completed_lessons=5,
            goal_count=2,
            published_posts=5,
            held_posts=0,
            blocked_posts=0,
        )
        assert rep_high.reputation_band == "helpful_contributor"

    def test_recommend_space_ids(self) -> None:
        spaces_starter = recommend_space_ids(
            persona_segment="starter",
            has_goal=True,
            completed_lessons=0,
        )
        assert "goal-planning-circle" in spaces_starter
        assert "goal-checkin-challenge" in spaces_starter

        spaces_investor = recommend_space_ids(
            persona_segment="beginner_investor",
            has_goal=False,
            completed_lessons=3,
        )
        assert "risk-literacy-circle" in spaces_investor
        assert "company-case-room" in spaces_investor

    def test_community_request_schemas(self) -> None:
        join_req = CommunityJoinRequest(session_id="session-user-001", space_id="general-space")
        assert join_req.space_id == "general-space"

        post_req = CommunityPostCreateRequest(
            session_id="session-user-001",
            space_id="general-space",
            title="Bài thảo luận mẫu",
            body="Nội dung thảo luận chi tiết có độ dài lớn hơn 10 ký tự.",
        )
        assert post_req.title == "Bài thảo luận mẫu"

        notif_req = CommunityNotificationStateRequest(action="read")
        assert notif_req.action == "read"
