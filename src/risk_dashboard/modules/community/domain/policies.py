from __future__ import annotations

import re

from risk_dashboard.modules.community.domain.entities import CommunityModerationDecision, CommunityReputation

BLOCK_PATTERNS = (
    ("pump_and_dump", re.compile(r"\b(mua ngay|all in|x2|x3|full margin|ăn bằng lần|vao lenh ngay)\b", re.I)),
    ("off_platform_lure", re.compile(r"\b(telegram|zalo|ib riêng|room riêng|link nhóm)\b", re.I)),
)

HOLD_PATTERNS = (
    ("direct_advice", re.compile(r"\b(nên mua|nên bán|giá mục tiêu|target giá|pick mã)\b", re.I)),
    ("spam_ticker", re.compile(r"\b[A-Z]{2,4}\b.*\b[A-Z]{2,4}\b.*\b[A-Z]{2,4}\b")),
    ("certainty_claim", re.compile(r"\b(chắc tăng|chắc ăn|bao lời|không thể giảm)\b", re.I)),
)


def moderate_post(
    *,
    title: str,
    body: str,
    space_type: str,
    recent_post_count: int,
) -> CommunityModerationDecision:
    text = f"{title}\n{body}".strip()
    labels: list[str] = []

    for label, pattern in BLOCK_PATTERNS:
        if pattern.search(text):
            labels.append(label)

    if labels:
        return CommunityModerationDecision(
            decision="blocked",
            labels=tuple(labels),
            explanation="Bài viết bị chặn vì có dấu hiệu hô hào giao dịch, kéo room ngoài hoặc thao túng.",
            escalation_level=3,
        )

    for label, pattern in HOLD_PATTERNS:
        if pattern.search(text):
            labels.append(label)

    if recent_post_count >= 3:
        labels.append("rate_limit_review")

    if space_type == "ask_expert" and not labels:
        labels.append("expert_queue")

    if labels:
        return CommunityModerationDecision(
            decision="held_for_review",
            labels=tuple(dict.fromkeys(labels)),
            explanation="Bài viết đã được giữ lại để review vì có dấu hiệu cần kiểm duyệt thêm.",
            escalation_level=2,
        )

    return CommunityModerationDecision(
        decision="published",
        labels=(),
        explanation="Bài viết đạt chuẩn public-safe của community.",
        escalation_level=0,
    )


def build_reputation(
    *,
    user_id: str,
    completed_lessons: int,
    goal_count: int,
    published_posts: int,
    held_posts: int,
    blocked_posts: int,
) -> CommunityReputation:
    learning_score = min(80, completed_lessons * 12 + goal_count * 8)
    contribution_score = max(0, min(80, published_posts * 15 - held_posts * 5 - blocked_posts * 20))
    strikes = blocked_posts

    if learning_score >= 55 and contribution_score >= 40:
        band = "helpful_contributor"
    elif learning_score >= 35:
        band = "consistent_learner"
    else:
        band = "learner"

    return CommunityReputation(
        user_id=user_id,
        learning_credibility_score=learning_score,
        contribution_quality_score=contribution_score,
        moderation_strike_count=strikes,
        reputation_band=band,
        trust_note=(
            "Điểm uy tín phản ánh mức độ học tập và đóng góp có chất lượng, không phải chứng nhận tư vấn đầu tư."
        ),
    )


def recommend_space_ids(
    *,
    persona_segment: str,
    has_goal: bool,
    completed_lessons: int,
) -> list[str]:
    recommended: list[str] = []
    if persona_segment in {"starter", "household_manager"}:
        recommended.append("goal-planning-circle")
    if persona_segment in {"beginner_investor", "advanced_pro"} or completed_lessons >= 2:
        recommended.append("risk-literacy-circle")
        recommended.append("company-case-room")
    if has_goal:
        recommended.append("goal-checkin-challenge")
    return list(dict.fromkeys(recommended))
