from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.admin_cms.infrastructure.repositories.sqlite import reset_admin_cms_state
from risk_dashboard.modules.community.infrastructure.repositories.sqlite import reset_community_state
from risk_dashboard.modules.financial_health.infrastructure.repositories.sqlite import (
    reset_financial_health_state,
)
from risk_dashboard.modules.goals.infrastructure.repositories.sqlite import reset_goals_state
from risk_dashboard.modules.home_onboarding.infrastructure.repositories.sqlite import (
    reset_home_onboarding_state,
)
from risk_dashboard.modules.learning.infrastructure.repositories.sqlite import reset_learning_state


def _content_ops_headers(role: str) -> dict[str, str]:
    return {
        "X-Admin-Content-Ops-Key": "content-ops-test",
        "X-Content-Ops-Role": role,
    }


def test_community_public_safe_flow():
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_goals_state()
    reset_learning_state()
    reset_community_state()
    reset_admin_cms_state()
    client = TestClient(app)

    session_id = client.post("/api/v1/public/onboarding/start").json()["session_id"]
    complete = client.post(
        "/api/v1/public/onboarding/complete",
        json={
            "session_id": session_id,
            "answers": [
                {"question_key": "primary_goal", "answer_value": "manage_household_money"},
                {"question_key": "knowledge_level", "answer_value": "basic"},
                {"question_key": "primary_interest", "answer_value": "cashflow"},
                {"question_key": "current_state", "answer_value": "income_no_long_term_plan"},
                {"question_key": "risk_tolerance_prelim", "answer_value": "moderate"},
            ],
        },
    )
    assert complete.status_code == 200

    created_goal = client.post(
        "/api/v1/public/goals",
        json={
            "session_id": session_id,
            "goal_type": "emergency_fund",
            "goal_name": "Quy du phong gia dinh",
            "deadline": "2027-04-30",
            "target_amount": 36000000,
            "current_amount": 6000000,
            "priority": "high",
            "currency": "VND",
            "base_currency": "VND",
            "confidence_level": "estimated",
        },
    )
    assert created_goal.status_code == 200

    home = client.get(f"/api/v1/public/community/home?session_id={session_id}")
    assert home.status_code == 200
    payload = home.json()
    assert payload["spaces"]
    assert "goal-planning-circle" in payload["recommended_space_ids"]
    assert payload["reputation"]["reputation_band"] in {"learner", "consistent_learner", "helpful_contributor"}
    assert payload["challenge_progress"]
    assert payload["notifications"]
    notification_id = payload["notifications"][0]["notification_id"]

    public_home = client.get(f"/api/v1/public/home/{session_id}")
    assert public_home.status_code == 200
    assert public_home.json()["community_snapshot"]["next_action_path"].startswith("/community")
    assert public_home.json()["community_snapshot"]["active_notification_count"] >= 1

    mark_read = client.post(
        f"/api/v1/public/community/notifications/{notification_id}/state",
        json={"action": "read"},
    )
    assert mark_read.status_code == 200
    assert mark_read.json()["status"] == "read"

    home_after_read = client.get(f"/api/v1/public/community/home?session_id={session_id}")
    assert home_after_read.status_code == 200
    assert all(item["notification_id"] != notification_id for item in home_after_read.json()["notifications"])
    if home_after_read.json()["notifications"]:
        dismiss_id = home_after_read.json()["notifications"][0]["notification_id"]
        dismiss = client.post(
            f"/api/v1/public/community/notifications/{dismiss_id}/state",
            json={"action": "dismiss"},
        )
        assert dismiss.status_code == 200
        assert dismiss.json()["status"] == "dismissed"

    joined = client.post(
        "/api/v1/public/community/spaces/join",
        json={"session_id": session_id, "space_id": "goal-planning-circle"},
    )
    assert joined.status_code == 200
    assert joined.json()["space_id"] == "goal-planning-circle"

    published = client.post(
        "/api/v1/public/community/spaces/posts",
        json={
            "session_id": session_id,
            "space_id": "goal-planning-circle",
            "post_type": "discussion",
            "title": "Trade-off cho goal quy du phong",
            "body": "Minh muon hoc cach uu tien pace tich luy va giu ky luat check-in goal ma khong bi qua suc.",
        },
    )
    assert published.status_code == 200
    assert published.json()["moderation_status"] == "published"

    posts = client.get("/api/v1/public/community/spaces/goal-planning-circle/posts")
    assert posts.status_code == 200
    assert len(posts.json()) == 1
    post_id = posts.json()[0]["post_id"]

    comment = client.post(
        "/api/v1/public/community/spaces/comments",
        json={
            "session_id": session_id,
            "post_id": post_id,
            "body": "Minh dong y voi cach tiep can pace va muon them lesson ve goal check-in.",
        },
    )
    assert comment.status_code == 200
    assert comment.json()["moderation_status"] == "published"

    reply = client.post(
        "/api/v1/public/community/spaces/comments",
        json={
            "session_id": session_id,
            "post_id": post_id,
            "parent_comment_id": comment.json()["comment_id"],
            "body": "Reply them de giu thread theo huong hoc tap va co cau truc hon.",
        },
    )
    assert reply.status_code == 200
    assert reply.json()["thread_depth"] == 1

    posts_with_comment = client.get("/api/v1/public/community/spaces/goal-planning-circle/posts")
    assert posts_with_comment.status_code == 200
    assert len(posts_with_comment.json()[0]["comments"]) == 1
    assert len(posts_with_comment.json()[0]["comments"][0]["replies"]) == 1

    blocked = client.post(
        "/api/v1/public/community/spaces/posts",
        json={
            "session_id": session_id,
            "space_id": "goal-planning-circle",
            "post_type": "discussion",
            "title": "Mua ngay ma nay",
            "body": "FPT mua ngay all in x2 x3, vao room rieng telegram de nhan lenh.",
        },
    )
    assert blocked.status_code == 200
    assert blocked.json()["moderation_status"] == "blocked"
    assert "pump_and_dump" in blocked.json()["moderation_labels"]

    join_expert = client.post(
        "/api/v1/public/community/spaces/join",
        json={"session_id": session_id, "space_id": "ask-an-expert-weekly"},
    )
    assert join_expert.status_code == 200

    held = client.post(
        "/api/v1/public/community/spaces/posts",
        json={
            "session_id": session_id,
            "space_id": "ask-an-expert-weekly",
            "post_type": "question",
            "title": "Nen mua ma nao cho nguoi moi?",
            "body": "Minh muon hoi nen mua ma nao va gia muc tieu co hop ly khong.",
        },
    )
    assert held.status_code == 200
    assert held.json()["moderation_status"] == "held_for_review"

    queue = client.get(
        "/api/v1/public/community/moderation/queue",
        headers={"X-Community-Moderator-Key": "community-dev"},
    )
    assert queue.status_code == 200
    assert queue.json()
    assert queue.json()[0]["content_type"] == "post"

    queue_filtered = client.get(
        "/api/v1/public/community/moderation/queue",
        params={"space_id": "ask-an-expert-weekly", "search": "gia muc tieu"},
        headers={"X-Community-Moderator-Key": "community-dev"},
    )
    assert queue_filtered.status_code == 200
    assert queue_filtered.json()
    risk_label = queue_filtered.json()[0]["ai_risk_labels"][0]

    queue_by_label = client.get(
        "/api/v1/public/community/moderation/queue",
        params={"risk_label": risk_label},
        headers={"X-Community-Moderator-Key": "community-dev"},
    )
    assert queue_by_label.status_code == 200
    assert queue_by_label.json()

    review = client.post(
        "/api/v1/public/community/moderation/review",
        headers={"X-Community-Moderator-Key": "community-dev"},
        json={
            "content_type": "post",
            "content_id": held.json()["post_id"],
            "action": "publish",
            "reviewer_id": "moderator-test",
            "notes": "Cho phep vi da sua de theo huong hoi framework.",
        },
    )
    assert review.status_code == 200
    assert review.json()["decision"] == "published"


def test_community_uses_published_policy_snippet_from_content_ops(monkeypatch):
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_goals_state()
    reset_learning_state()
    reset_community_state()
    reset_admin_cms_state()
    monkeypatch.setenv("ADMIN_CONTENT_OPS_KEY", "content-ops-test")
    client = TestClient(app)

    draft = client.put(
        "/admin/cms/content/community_policy_snippet/new",
        headers=_content_ops_headers("moderator"),
        json={
            "slug": "community-trust-first",
            "title": "Trust-first policy",
            "locale": "vi-VN",
            "owner_team": "community",
            "risk_category": "policy",
            "payload": {
                "surface": "community",
                "policy_type": "posting_rule",
                "body": "Community public chỉ để học cùng và chia sẻ có kiểm soát; mọi certainty claim sẽ bị chặn.",
                "risk_tags": ["trust_first", "anti_hype"],
            },
            "change_summary": "community policy runtime",
        },
    )
    assert draft.status_code == 200
    content_id = draft.json()["content_id"]
    assert client.post(
        f"/admin/cms/content/{content_id}/submit-review",
        headers=_content_ops_headers("moderator"),
        json={"comments": "ready"},
    ).status_code == 200
    assert client.post(
        f"/admin/cms/content/{content_id}/approve",
        headers=_content_ops_headers("compliance_reviewer"),
        json={"comments": "approved"},
    ).status_code == 200
    assert client.post(
        f"/admin/cms/content/{content_id}/publish",
        headers=_content_ops_headers("admin"),
        json={"comments": "publish"},
    ).status_code == 200

    session_id = client.post("/api/v1/public/onboarding/start").json()["session_id"]
    complete = client.post(
        "/api/v1/public/onboarding/complete",
        json={
            "session_id": session_id,
            "answers": [
                {"question_key": "primary_goal", "answer_value": "manage_household_money"},
                {"question_key": "knowledge_level", "answer_value": "basic"},
                {"question_key": "primary_interest", "answer_value": "cashflow"},
                {"question_key": "current_state", "answer_value": "income_no_long_term_plan"},
                {"question_key": "risk_tolerance_prelim", "answer_value": "moderate"},
            ],
        },
    )
    assert complete.status_code == 200

    home = client.get(f"/api/v1/public/community/home?session_id={session_id}")
    assert home.status_code == 200
    assert (
        "Community public chỉ để học cùng và chia sẻ có kiểm soát; mọi certainty claim sẽ bị chặn."
        in home.json()["policy_highlights"]
    )


def test_community_uses_disclaimer_and_contextual_explainer_from_content_ops(monkeypatch):
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_goals_state()
    reset_learning_state()
    reset_community_state()
    reset_admin_cms_state()
    monkeypatch.setenv("ADMIN_CONTENT_OPS_KEY", "content-ops-test")
    client = TestClient(app)

    disclaimer = client.put(
        "/admin/cms/content/disclaimer_block/new",
        headers=_content_ops_headers("editor"),
        json={
            "slug": "community-home-disclaimer",
            "title": "Community disclaimer",
            "locale": "vi-VN",
            "owner_team": "compliance",
            "risk_category": "legal",
            "payload": {
                "surface": "community",
                "topic": "community_home",
                "short_text": "Community nay de hoc va chia se co kiem soat, khong phai room tin hieu.",
                "full_text": "Community nay de hoc va chia se co kiem soat, khong phai room tin hieu hay noi keu goi giao dich.",
                "severity": "high",
            },
            "change_summary": "community disclaimer",
        },
    )
    assert disclaimer.status_code == 200
    disclaimer_id = disclaimer.json()["content_id"]
    assert client.post(f"/admin/cms/content/{disclaimer_id}/submit-review", headers=_content_ops_headers("editor"), json={}).status_code == 200
    assert client.post(f"/admin/cms/content/{disclaimer_id}/approve", headers=_content_ops_headers("compliance_reviewer"), json={}).status_code == 200
    assert client.post(f"/admin/cms/content/{disclaimer_id}/publish", headers=_content_ops_headers("admin"), json={}).status_code == 200

    explainer = client.put(
        "/admin/cms/content/contextual_explainer/new",
        headers=_content_ops_headers("editor"),
        json={
            "slug": "goal-planning-circle",
            "title": "Vì sao Goal Planning Circle phù hợp",
            "locale": "vi-VN",
            "owner_team": "education",
            "risk_category": "education",
            "payload": {
                "surface": "community",
                "trigger_key": "goal-planning-circle",
                "title": "Vì sao Goal Planning Circle phù hợp",
                "body": ["Space nay hop khi ban muon hoc pace tich luy va trade-off doi song mot cach binh tinh."],
                "linked_lesson_ids": ["goal-planning-basics-101"],
                "guardrail_note": "Khong can chia se thong tin tai chinh nhay cam de tham gia.",
            },
            "change_summary": "community explainer",
        },
    )
    assert explainer.status_code == 200
    explainer_id = explainer.json()["content_id"]
    assert client.post(f"/admin/cms/content/{explainer_id}/submit-review", headers=_content_ops_headers("editor"), json={}).status_code == 200
    assert client.post(f"/admin/cms/content/{explainer_id}/approve", headers=_content_ops_headers("reviewer"), json={}).status_code == 200
    assert client.post(f"/admin/cms/content/{explainer_id}/publish", headers=_content_ops_headers("admin"), json={}).status_code == 200

    session_id = client.post("/api/v1/public/onboarding/start").json()["session_id"]
    complete = client.post(
        "/api/v1/public/onboarding/complete",
        json={
            "session_id": session_id,
            "answers": [
                {"question_key": "primary_goal", "answer_value": "manage_household_money"},
                {"question_key": "knowledge_level", "answer_value": "basic"},
                {"question_key": "primary_interest", "answer_value": "cashflow"},
                {"question_key": "current_state", "answer_value": "income_no_long_term_plan"},
                {"question_key": "risk_tolerance_prelim", "answer_value": "moderate"},
            ],
        },
    )
    assert complete.status_code == 200

    home = client.get(f"/api/v1/public/community/home?session_id={session_id}")
    assert home.status_code == 200
    payload = home.json()
    assert payload["disclaimer"]["short_text"] == "Community nay de hoc va chia se co kiem soat, khong phai room tin hieu."
    assert payload["contextual_explainer"]["title"] == "Vì sao Goal Planning Circle phù hợp"
