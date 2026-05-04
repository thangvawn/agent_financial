from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.admin_cms.infrastructure.repositories.sqlite import reset_admin_cms_state


def _headers(role: str) -> dict[str, str]:
    return {
        "X-Admin-Content-Ops-Key": "content-ops-test",
        "X-Content-Ops-Role": role,
    }


def test_admin_cms_workflow_and_analytics(monkeypatch):
    reset_admin_cms_state()
    monkeypatch.setenv("ADMIN_CONTENT_OPS_KEY", "content-ops-test")
    client = TestClient(app)

    status = client.get("/admin/cms/status", headers=_headers("admin"))
    assert status.status_code == 200
    assert "lesson" in status.json()["supported_content_types"]
    assert "path" in status.json()["supported_content_types"]

    draft = client.put(
        "/admin/cms/content/lesson/new",
        headers=_headers("editor"),
        json={
            "slug": "money-basics-ops",
            "title": "Money Basics Ops",
            "locale": "vi-VN",
            "owner_team": "education",
            "risk_category": "education",
            "payload": {"title": "Money Basics Ops", "body": ["Micro lesson body"]},
            "change_summary": "initial draft",
        },
    )
    assert draft.status_code == 200
    content_id = draft.json()["content_id"]
    assert draft.json()["workflow_state"] == "draft"

    submit = client.post(
        f"/admin/cms/content/{content_id}/submit-review",
        headers=_headers("editor"),
        json={"comments": "ready for review"},
    )
    assert submit.status_code == 200
    assert submit.json()["workflow_state"] == "review"

    review_queue = client.get("/admin/cms/review-queue", headers=_headers("reviewer"))
    assert review_queue.status_code == 200
    assert any(item["content_id"] == content_id for item in review_queue.json())

    approved = client.post(
        f"/admin/cms/content/{content_id}/approve",
        headers=_headers("reviewer"),
        json={"comments": "clear enough for publish"},
    )
    assert approved.status_code == 200
    assert approved.json()["workflow_state"] == "approved"

    published = client.post(
        f"/admin/cms/content/{content_id}/publish",
        headers=_headers("admin"),
        json={"comments": "publish now"},
    )
    assert published.status_code == 200
    assert published.json()["workflow_state"] == "published"

    analytics = client.post(
        f"/admin/cms/analytics/content/{content_id}/record",
        headers=_headers("admin"),
        json={"event_type": "open"},
    )
    assert analytics.status_code == 200
    assert analytics.json()["open_count"] == 1

    versions = client.get(f"/admin/cms/content/{content_id}/versions", headers=_headers("admin"))
    assert versions.status_code == 200
    assert versions.json()[0]["version_number"] >= 1


def test_admin_cms_compliance_and_ai_draft_guardrails(monkeypatch):
    reset_admin_cms_state()
    monkeypatch.setenv("ADMIN_CONTENT_OPS_KEY", "content-ops-test")
    client = TestClient(app)

    ai_draft = client.post(
        "/admin/cms/ai/generate-draft",
        headers=_headers("editor"),
        json={
            "content_type": "disclaimer_block",
            "title": "Investing Disclaimer",
            "prompt": "Nha soan thao disclaimer ngan gon cho public safe investing explainer.",
            "locale": "vi-VN",
            "owner_team": "compliance",
            "risk_category": "legal",
        },
    )
    assert ai_draft.status_code == 200
    content_id = ai_draft.json()["content_id"]
    assert ai_draft.json()["workflow_state"] == "draft"
    assert ai_draft.json()["latest_origin"] == "ai_assisted"

    publish_direct = client.post(
        f"/admin/cms/content/{content_id}/publish",
        headers=_headers("admin"),
        json={"comments": "should fail"},
    )
    assert publish_direct.status_code == 400

    submit = client.post(
        f"/admin/cms/content/{content_id}/submit-review",
        headers=_headers("editor"),
        json={"comments": "needs compliance"},
    )
    assert submit.status_code == 200
    assert submit.json()["workflow_state"] == "review"

    reviewer_fail = client.post(
        f"/admin/cms/content/{content_id}/approve",
        headers=_headers("reviewer"),
        json={"comments": "not enough"},
    )
    assert reviewer_fail.status_code == 400

    compliance_ok = client.post(
        f"/admin/cms/content/{content_id}/approve",
        headers=_headers("compliance_reviewer"),
        json={"comments": "approved by compliance"},
    )
    assert compliance_ok.status_code == 200
    assert compliance_ok.json()["workflow_state"] == "approved"

    published = client.post(
        f"/admin/cms/content/{content_id}/publish",
        headers=_headers("admin"),
        json={"comments": "publish after compliance"},
    )
    assert published.status_code == 200
    assert published.json()["workflow_state"] == "published"
