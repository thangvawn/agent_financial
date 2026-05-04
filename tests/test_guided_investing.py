import json

from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.admin_cms.infrastructure.repositories.sqlite import reset_admin_cms_state
from risk_dashboard.modules.financial_health.infrastructure.repositories.sqlite import (
    reset_financial_health_state,
)
from risk_dashboard.modules.goals.infrastructure.repositories.sqlite import reset_goals_state
from risk_dashboard.modules.guided_investing.infrastructure.repositories.sqlite import (
    reset_guided_investing_state,
)
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


def test_guided_investing_public_flow(tmp_path, monkeypatch):
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_goals_state()
    reset_learning_state()
    reset_guided_investing_state()
    reset_admin_cms_state()
    monkeypatch.setenv("RISK_DASHBOARD_FINANCIALS_DIR", str(tmp_path / "financials"))
    client = TestClient(app)

    session_id = client.post("/api/v1/public/onboarding/start").json()["session_id"]
    complete = client.post(
        "/api/v1/public/onboarding/complete",
        json={
            "session_id": session_id,
            "answers": [
                {"question_key": "primary_goal", "answer_value": "learn_investing_safely"},
                {"question_key": "knowledge_level", "answer_value": "basic"},
                {"question_key": "primary_interest", "answer_value": "investing_basics"},
                {"question_key": "current_state", "answer_value": "already_saving_wants_to_invest"},
                {"question_key": "risk_tolerance_prelim", "answer_value": "balanced"},
            ],
        },
    )
    assert complete.status_code == 200

    health = client.post(
        "/api/v1/public/financial-health/assessment",
        json={
            "session_id": session_id,
            "monthly_income_range": "mid",
            "income_stability_level": "stable",
            "expense_discipline_level": "mostly_disciplined",
            "emergency_fund_months_band": "3_to_6m",
            "monthly_debt_payment_ratio_band": "lt_10pct",
            "savings_rate_band": "20_to_30pct",
            "liquidity_stress_level": "comfortable",
            "has_basic_insurance": True,
            "has_high_interest_debt": False,
            "wants_to_start_investing": True,
        },
    )
    assert health.status_code == 200
    assert health.json()["guided_investing_eligible"] is True

    learning_home = client.get(f"/api/v1/public/learning/home?session_id={session_id}")
    assert learning_home.status_code == 200
    first_lesson = learning_home.json()["next_lesson_id"]
    complete_first = client.post(f"/api/v1/public/learning/lessons/{first_lesson}/complete?session_id={session_id}")
    assert complete_first.status_code == 200
    learning_home_2 = client.get(f"/api/v1/public/learning/home?session_id={session_id}")
    second_lesson = learning_home_2.json()["next_lesson_id"]
    complete_second = client.post(f"/api/v1/public/learning/lessons/{second_lesson}/complete?session_id={session_id}")
    assert complete_second.status_code == 200

    eligibility = client.get(f"/api/v1/public/guided-investing/eligibility?session_id={session_id}")
    assert eligibility.status_code == 200
    assert eligibility.json()["eligible"] is True

    home = client.get(f"/api/v1/public/guided-investing/home?session_id={session_id}")
    assert home.status_code == 200
    assert home.json()["eligibility"]["eligible"] is True
    assert home.json()["watchlist_review"]["item_count"] == 0

    watch_item = client.post(
        "/api/v1/public/guided-investing/watchlist/items",
        json={
            "session_id": session_id,
            "ticker": "FPT",
            "label": "FPT - quan sat co ban",
            "reason_to_track": "Muon hoc company health va peer compare cua doanh nghiep cong nghe.",
            "theme_tag": "technology",
        },
    )
    assert watch_item.status_code == 200
    assert watch_item.json()["ticker"] == "FPT"

    watch_review = client.post(f"/api/v1/public/guided-investing/watchlist/review?session_id={session_id}")
    assert watch_review.status_code == 200
    assert watch_review.json()["item_count"] == 1

    save_portfolio = client.post(
        "/api/v1/public/guided-investing/portfolio/save",
        json={
            "session_id": session_id,
            "name": "Danh muc hoc tap",
            "holdings": [
                {"ticker": "FPT", "weight_pct": 55},
                {"ticker": "MWG", "weight_pct": 25},
                {"ticker": "VCB", "weight_pct": 20},
            ],
        },
    )
    assert save_portfolio.status_code == 200
    assert save_portfolio.json()["name"] == "Danh muc hoc tap"

    imported = client.post("/financials/import", json={"dataset": _load_sample_dataset().model_dump(mode="json")})
    assert imported.status_code == 200

    company = client.get("/api/v1/public/guided-investing/company/FPT")
    assert company.status_code == 200
    assert company.json()["ticker"] == "FPT"
    assert company.json()["headline"]

    portfolio = client.post(
        "/api/v1/public/guided-investing/portfolio/review",
        json={
            "session_id": session_id,
            "scenario_label": "stress_case",
            "holdings": [
                {"ticker": "FPT", "weight_pct": 55},
                {"ticker": "MWG", "weight_pct": 25},
                {"ticker": "VCB", "weight_pct": 20},
            ],
        },
    )
    assert portfolio.status_code == 200
    assert portfolio.json()["warnings"]

    saved_portfolio = client.get(f"/api/v1/public/guided-investing/portfolio?session_id={session_id}")
    assert saved_portfolio.status_code == 200
    assert saved_portfolio.json()["holdings"]

    history = client.get(f"/api/v1/public/guided-investing/portfolio/history?session_id={session_id}")
    assert history.status_code == 200
    assert history.json()
    assert history.json()[0]["scenario_label"] == "stress_case"

    journal = client.post(
        "/api/v1/public/guided-investing/journal",
        json={
            "session_id": session_id,
            "ticker": "FPT",
            "title": "Thesis FPT dau tien",
            "thesis": "Doanh nghiep nay co chat luong hoat dong va kha nang tao dong tien kha tot.",
            "uncertainties": "Chua ro muc dinh gia va rui ro tang truong cham lai.",
            "review_condition": "Xem lai neu company health xau di hoac market context sang high risk.",
        },
    )
    assert journal.status_code == 200
    assert journal.json()["ticker"] == "FPT"

    journals = client.get(f"/api/v1/public/guided-investing/journal?session_id={session_id}")
    assert journals.status_code == 200
    assert len(journals.json()) == 1

    safe_chat = client.post(
        "/api/v1/public/guided-investing/safe-chat",
        json={"session_id": session_id, "prompt": "Ma nao nen mua luc nay?"},
    )
    assert safe_chat.status_code == 200
    assert safe_chat.json()["allowed"] is False

    market_context = client.get("/api/v1/public/guided-investing/market-context")
    assert market_context.status_code == 200
    assert market_context.json()["headline"]


def test_guided_investing_uses_content_ops_disclaimer_and_contextual_explainer(tmp_path, monkeypatch):
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_goals_state()
    reset_learning_state()
    reset_guided_investing_state()
    reset_admin_cms_state()
    monkeypatch.setenv("RISK_DASHBOARD_FINANCIALS_DIR", str(tmp_path / "financials"))
    monkeypatch.setenv("ADMIN_CONTENT_OPS_KEY", "content-ops-test")
    client = TestClient(app)

    disclaimer = client.put(
        "/admin/cms/content/disclaimer_block/new",
        headers=_content_ops_headers("editor"),
        json={
            "slug": "guided-market-context-disclaimer",
            "title": "Guided Investing disclaimer",
            "locale": "vi-VN",
            "owner_team": "compliance",
            "risk_category": "legal",
            "payload": {
                "surface": "guided_investing",
                "topic": "market_context",
                "short_text": "Context nay de giai thich rui ro, khong phai khuyen nghi mua ban.",
                "full_text": "Context nay de giai thich rui ro, khong phai khuyen nghi mua ban hay du bao chac chan.",
                "severity": "high",
            },
            "change_summary": "guided disclaimer",
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
            "slug": "market_context",
            "title": "Doc market context dung cach",
            "locale": "vi-VN",
            "owner_team": "education",
            "risk_category": "education",
            "payload": {
                "surface": "guided_investing",
                "trigger_key": "market_context",
                "title": "Doc market context dung cach",
                "body": ["Hay doc market context nhu boi canh, khong phai lenh hanh dong."],
                "linked_lesson_ids": ["tool-risk-score-101"],
                "guardrail_note": "Neu chua chac, quay lai Learn Hub truoc.",
            },
            "change_summary": "guided explainer",
        },
    )
    assert explainer.status_code == 200
    explainer_id = explainer.json()["content_id"]
    assert client.post(f"/admin/cms/content/{explainer_id}/submit-review", headers=_content_ops_headers("editor"), json={}).status_code == 200
    assert client.post(f"/admin/cms/content/{explainer_id}/approve", headers=_content_ops_headers("reviewer"), json={}).status_code == 200
    assert client.post(f"/admin/cms/content/{explainer_id}/publish", headers=_content_ops_headers("admin"), json={}).status_code == 200

    response = client.get("/api/v1/public/guided-investing/market-context")
    assert response.status_code == 200
    payload = response.json()
    assert payload["disclaimer"]["short_text"] == "Context nay de giai thich rui ro, khong phai khuyen nghi mua ban."
    assert payload["contextual_explainer"]["title"] == "Doc market context dung cach"
