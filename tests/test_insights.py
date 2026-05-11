import json

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
from risk_dashboard.schemas.financials import FinancialDataset


def _content_ops_headers(role: str) -> dict[str, str]:
    return {
        "X-Admin-Content-Ops-Key": "content-ops-test",
        "X-Content-Ops-Role": role,
    }


def _load_sample_dataset() -> FinancialDataset:
    with open("tests/fixtures/sample_financial_dataset.json", "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return FinancialDataset.model_validate(payload)


def test_insights_home_supports_advanced_persona_and_company_context(tmp_path, monkeypatch):
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_learning_state()
    reset_goals_state()
    reset_admin_cms_state()
    monkeypatch.setenv("RISK_DASHBOARD_FINANCIALS_DIR", str(tmp_path / "financials"))
    client = TestClient(app)

    session_id = client.post("/api/v1/public/onboarding/start").json()["session_id"]
    complete = client.post(
        "/api/v1/public/onboarding/complete",
        json={
            "session_id": session_id,
            "answers": [
                {"question_key": "primary_goal", "answer_value": "deep_analysis_tools"},
                {"question_key": "knowledge_level", "answer_value": "advanced"},
                {"question_key": "primary_interest", "answer_value": "markets"},
                {"question_key": "current_state", "answer_value": "already_investing_wants_structure"},
                {"question_key": "risk_tolerance_prelim", "answer_value": "advanced"},
            ],
        },
    )
    assert complete.status_code == 200
    assert complete.json()["primary_route"] == "insights"

    home = client.get(f"/api/v1/public/home/{session_id}")
    assert home.status_code == 200
    assert home.json()["next_best_action_ref"] == "/insights"

    imported = client.post("/financials/import", json={"dataset": _load_sample_dataset().model_dump(mode="json")})
    assert imported.status_code == 200

    insights = client.get(f"/api/v1/public/insights/home?session_id={session_id}&ticker=FPT")
    assert insights.status_code == 200
    payload = insights.json()
    assert payload["level"] == "pro"
    assert payload["market_regime_snapshot"]["headline"]
    assert payload["cross_asset_context"]["headline"]
    assert payload["company_health_insight"]["title"] == "Company Health: FPT"
    assert payload["scenario_what_if"]["title"] == "Scenario What-if"
    assert payload["explainability_top_drivers"]["title"] == "Explainability / Top Drivers"


def test_insights_dashboard_contract_contains_safety_quality_and_normalized_series():
    client = TestClient(app)

    response = client.get("/api/v1/public/insights/dashboard?range=1M")
    assert response.status_code == 200
    payload = response.json()

    assert isinstance(payload["market_summary"]["regime"], str)
    assert len(payload["market_summary"]["regime"]) >= 3
    assert payload["safety"]["no_buy_sell_recommendation"] is True
    assert "khuyến nghị mua/bán" in payload["safety"]["disclaimer"]
    assert payload["data_quality"]["overall_freshness"] in {"fresh", "delayed", "stale", "unavailable"}
    assert payload["data_quality"]["sources"]
    assert payload["market_narrative"]["key_points"]
    assert payload["market_narrative"]["caveats"]

    first_series = payload["cross_asset_pulse"]["series"][0]
    assert first_series["normalized_base"] == 100
    assert first_series["values"][0]["normalized_value"] == 100
    assert first_series["freshness_status"] in {"fresh", "delayed", "stale", "unavailable"}

    assert all("probability" in scenario and "impact_level" in scenario for scenario in payload["scenario_monitor"])
    assert payload["watchlist_impact"]["state"] == "empty"
    assert payload["learn_links"]


def test_insight_scenario_endpoint_accepts_overrides():
    client = TestClient(app)
    response = client.get("/api/v1/public/insights/scenario?level=basic&usd_vnd_rate=26000&sbv_interest_rate_pct=4.5")
    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Scenario What-if"
    assert payload["headline"]


def test_insights_use_content_ops_disclaimer_and_contextual_explainer(tmp_path, monkeypatch):
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_learning_state()
    reset_goals_state()
    reset_admin_cms_state()
    monkeypatch.setenv("RISK_DASHBOARD_FINANCIALS_DIR", str(tmp_path / "financials"))
    monkeypatch.setenv("ADMIN_CONTENT_OPS_KEY", "content-ops-test")
    client = TestClient(app)

    disclaimer = client.put(
        "/admin/cms/content/disclaimer_block/new",
        headers=_content_ops_headers("editor"),
        json={
            "slug": "insights-market-regime-disclaimer",
            "title": "Insights disclaimer",
            "locale": "vi-VN",
            "owner_team": "compliance",
            "risk_category": "legal",
            "payload": {
                "surface": "insights",
                "topic": "market_regime_snapshot",
                "short_text": "Insight nay de doc boi canh, khong phai noi dung giat gan.",
                "full_text": "Insight nay de doc boi canh, khong phai noi dung giat gan hay khuyen nghi dau tu.",
                "severity": "medium",
            },
            "change_summary": "insights disclaimer",
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
            "slug": "market_regime_snapshot",
            "title": "How to read market regime",
            "locale": "vi-VN",
            "owner_team": "education",
            "risk_category": "education",
            "payload": {
                "surface": "insights",
                "trigger_key": "market_regime_snapshot",
                "title": "How to read market regime",
                "body": ["Doc regime de hieu nhiet do rui ro, khong phai de doan gia ngay mai."],
                "linked_lesson_ids": ["drawdown-basics-101"],
                "guardrail_note": "Neu ban moi, hay hoc Risk Basics truoc.",
            },
            "change_summary": "insights explainer",
        },
    )
    assert explainer.status_code == 200
    explainer_id = explainer.json()["content_id"]
    assert client.post(f"/admin/cms/content/{explainer_id}/submit-review", headers=_content_ops_headers("editor"), json={}).status_code == 200
    assert client.post(f"/admin/cms/content/{explainer_id}/approve", headers=_content_ops_headers("reviewer"), json={}).status_code == 200
    assert client.post(f"/admin/cms/content/{explainer_id}/publish", headers=_content_ops_headers("admin"), json={}).status_code == 200

    response = client.get("/api/v1/public/insights/home?level=basic&ticker=FPT")
    assert response.status_code == 200
    payload = response.json()
    assert payload["market_regime_snapshot"]["disclaimer"]["short_text"] == "Insight nay de doc boi canh, khong phai noi dung giat gan."
    assert payload["market_regime_snapshot"]["contextual_explainer"]["title"] == "How to read market regime"
