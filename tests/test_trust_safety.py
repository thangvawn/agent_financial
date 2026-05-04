from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.admin_cms.infrastructure.repositories.sqlite import reset_admin_cms_state
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


def _trust_headers() -> dict[str, str]:
    return {"X-Admin-Trust-Safety-Key": "trust-test"}


def _complete_basic_onboarding(client: TestClient) -> str:
    session_id = client.post("/api/v1/public/onboarding/start").json()["session_id"]
    complete = client.post(
        "/api/v1/public/onboarding/complete",
        json={
            "session_id": session_id,
            "answers": [
                {"question_key": "primary_goal", "answer_value": "understand_finance_basics"},
                {"question_key": "knowledge_level", "answer_value": "beginner"},
                {"question_key": "primary_interest", "answer_value": "basics"},
                {"question_key": "current_state", "answer_value": "no_clear_financial_system"},
                {"question_key": "risk_tolerance_prelim", "answer_value": "very_cautious"},
            ],
        },
    )
    assert complete.status_code == 200
    return session_id


def test_trust_safety_tracks_ai_privacy_block_and_runtime_disclaimer_injection(monkeypatch):
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_goals_state()
    reset_learning_state()
    reset_admin_cms_state()
    monkeypatch.setenv("ADMIN_TRUST_SAFETY_KEY", "trust-test")
    client = TestClient(app)

    session_id = _complete_basic_onboarding(client)

    blocked = client.post(
        "/api/v1/public/ai-assistant/respond",
        json={
            "session_id": session_id,
            "surface": "learning",
            "prompt": "So tai khoan 123456 va OTP 999999 cua toi co an toan khong?",
        },
    )
    assert blocked.status_code == 200
    blocked_payload = blocked.json()
    assert blocked_payload["allowed"] is False
    assert blocked_payload["route_decision"] == "blocked_for_privacy"
    assert "pii_or_privacy_issue" in blocked_payload["risk_labels"]

    insights = client.get("/api/v1/public/insights/home?level=basic&ticker=FPT")
    assert insights.status_code == 200
    insight_payload = insights.json()["market_regime_snapshot"]
    assert insight_payload["disclaimer"]["short_text"]
    assert insight_payload["confidence_label"]
    assert insight_payload["what_this_is"]
    assert insight_payload["what_this_is_not"]

    status = client.get("/admin/trust-safety/status", headers=_trust_headers())
    assert status.status_code == 200
    assert status.json()["total_events"] >= 2
    assert status.json()["default_disclaimer_injections"] >= 1

    privacy_audit = client.get("/admin/trust-safety/audit?surface=learning", headers=_trust_headers())
    assert privacy_audit.status_code == 200
    assert any("pii_or_privacy_issue" in item["risk_classes"] for item in privacy_audit.json())

    disclaimer_audit = client.get(
        "/admin/trust-safety/audit?surface=insights&risk_class=missing_disclaimer",
        headers=_trust_headers(),
    )
    assert disclaimer_audit.status_code == 200
    assert disclaimer_audit.json()


def test_trust_safety_tracks_community_block_and_cms_ai_draft(monkeypatch):
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_goals_state()
    reset_learning_state()
    reset_admin_cms_state()
    monkeypatch.setenv("ADMIN_TRUST_SAFETY_KEY", "trust-test")
    monkeypatch.setenv("ADMIN_CONTENT_OPS_KEY", "content-ops-test")
    client = TestClient(app)

    session_id = _complete_basic_onboarding(client)
    join = client.post(
        "/api/v1/public/community/spaces/join",
        json={"session_id": session_id, "space_id": "goal-planning-circle"},
    )
    assert join.status_code == 200

    post = client.post(
        "/api/v1/public/community/spaces/posts",
        json={
            "session_id": session_id,
            "space_id": "goal-planning-circle",
            "post_type": "discussion",
            "title": "Moi nguoi xem ho minh",
            "body": "Day la so dien thoai 0909123456 va CCCD 012345678912, ai can thi vao telegram room rieng.",
        },
    )
    assert post.status_code == 200
    post_payload = post.json()
    assert post_payload["moderation_status"] == "blocked"
    assert "pii_or_privacy_issue" in post_payload["moderation_labels"]

    ai_draft = client.post(
        "/admin/cms/ai/generate-draft",
        headers=_content_ops_headers("editor"),
        json={
            "content_type": "disclaimer_block",
            "title": "Trust disclaimer",
            "prompt": "Soan draft disclaimer ngan gon cho public investing explainer.",
            "locale": "vi-VN",
            "owner_team": "compliance",
            "risk_category": "legal",
        },
    )
    assert ai_draft.status_code == 200
    assert ai_draft.json()["workflow_state"] == "draft"
    assert ai_draft.json()["latest_origin"] == "ai_assisted"

    community_audit = client.get("/admin/trust-safety/audit?surface=community", headers=_trust_headers())
    assert community_audit.status_code == 200
    assert any("pii_or_privacy_issue" in item["risk_classes"] for item in community_audit.json())

    cms_audit = client.get("/admin/trust-safety/audit?surface=admin_cms", headers=_trust_headers())
    assert cms_audit.status_code == 200
    assert any(item["route_decision"] == "draft_only_guardrail" for item in cms_audit.json())

    open_incident = client.post(
        "/admin/trust-safety/incidents/open",
        headers=_trust_headers(),
        json={
            "source_audit_id": community_audit.json()[0]["audit_id"],
            "surface": "community",
            "topic": "community_post",
            "severity": "critical",
            "summary": "Community post chứa PII và lure ra kênh ngoài.",
            "owner_id": "mod-team",
            "notes": "Cần review pattern và chặn user nếu tái phạm.",
        },
    )
    assert open_incident.status_code == 200
    incident_id = open_incident.json()["incident_id"]
    assert open_incident.json()["status"] == "open"

    investigate = client.post(
        f"/admin/trust-safety/incidents/{incident_id}/action",
        headers=_trust_headers(),
        json={"action": "investigate", "owner_id": "mod-team", "notes": "Đang điều tra."},
    )
    assert investigate.status_code == 200
    assert investigate.json()["status"] == "investigating"

    resolve = client.post(
        f"/admin/trust-safety/incidents/{incident_id}/action",
        headers=_trust_headers(),
        json={"action": "resolve", "notes": "Đã chặn nội dung và theo dõi thêm."},
    )
    assert resolve.status_code == 200
    assert resolve.json()["status"] == "resolved"
    assert resolve.json()["resolved_at"] is not None

    incidents = client.get("/admin/trust-safety/incidents?surface=community", headers=_trust_headers())
    assert incidents.status_code == 200
    assert any(item["incident_id"] == incident_id for item in incidents.json())

    filtered_audit = client.get(
        "/admin/trust-safety/audit?surface=community&severity=critical&search=telegram",
        headers=_trust_headers(),
    )
    assert filtered_audit.status_code == 200
    assert filtered_audit.json()

    filtered_incidents = client.get(
        "/admin/trust-safety/incidents?surface=community&severity=critical&status=resolved&search=PII",
        headers=_trust_headers(),
    )
    assert filtered_incidents.status_code == 200
    assert any(item["incident_id"] == incident_id for item in filtered_incidents.json())


def test_trust_safety_freezes_and_degrades_surface_from_active_incidents(monkeypatch):
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_goals_state()
    reset_learning_state()
    reset_admin_cms_state()
    monkeypatch.setenv("ADMIN_TRUST_SAFETY_KEY", "trust-test")
    client = TestClient(app)

    critical = client.post(
        "/admin/trust-safety/incidents/open",
        headers=_trust_headers(),
        json={
            "surface": "insights",
            "topic": "market_regime_snapshot",
            "severity": "critical",
            "summary": "Narrative quality incident dang duoc dieu tra.",
            "notes": "Freeze insights public.",
        },
    )
    assert critical.status_code == 200

    insights = client.get("/api/v1/public/insights/home?level=basic&ticker=FPT")
    assert insights.status_code == 200
    market_card = insights.json()["market_regime_snapshot"]
    assert market_card["confidence_label"] == "low_confidence"
    assert "freeze" in (market_card["risk_banner"] or "").lower()

    high = client.post(
        "/admin/trust-safety/incidents/open",
        headers=_trust_headers(),
        json={
            "surface": "guided_investing",
            "topic": "market_context",
            "severity": "high",
            "summary": "Guided investing dang can degrade de review wording.",
            "notes": "Degrade market context.",
        },
    )
    assert high.status_code == 200

    session_id = _complete_basic_onboarding(client)
    home = client.get("/api/v1/public/guided-investing/home", params={"session_id": session_id})
    assert home.status_code == 200
    payload = home.json()
    assert payload["risk_banner"] is not None
    assert "degraded" in payload["risk_banner"].lower()
