from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.admin_cms.infrastructure.repositories.sqlite import reset_admin_cms_state
from risk_dashboard.modules.financial_health.infrastructure.repositories.sqlite import (
    reset_financial_health_state,
)
from risk_dashboard.modules.goals.infrastructure.repositories.sqlite import (
    reset_goals_state,
)
from risk_dashboard.modules.home_onboarding.infrastructure.repositories.sqlite import (
    reset_home_onboarding_state,
)
from risk_dashboard.modules.learning.infrastructure.repositories.sqlite import (
    reset_learning_state,
)


def _content_ops_headers(role: str) -> dict[str, str]:
    return {
        "X-Admin-Content-Ops-Key": "content-ops-test",
        "X-Content-Ops-Role": role,
    }


def test_onboarding_flow_routes_starter_to_learn():
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_learning_state()
    reset_goals_state()
    reset_admin_cms_state()
    client = TestClient(app)

    start = client.post("/api/v1/public/onboarding/start")
    assert start.status_code == 200
    session_id = start.json()["session_id"]

    answer = client.post(
        "/api/v1/public/onboarding/answer",
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
    assert answer.status_code == 200

    complete = client.post(
        "/api/v1/public/onboarding/complete",
        json={"session_id": session_id, "answers": []},
    )
    assert complete.status_code == 200
    payload = complete.json()
    assert payload["persona_segment"] == "starter"
    assert payload["primary_route"] == "learn"
    assert payload["guided_investing_eligible"] is False

    home = client.get(f"/api/v1/public/home/{session_id}")
    assert home.status_code == 200
    body = home.json()
    assert body["next_best_action_type"] == "continue_learning_path"
    assert any(block["block_id"] == "learning_recommendation" for block in body["blocks"])
    learning = client.get(f"/api/v1/public/learning/home?session_id={session_id}")
    assert learning.status_code == 200
    assert learning.json()["path_id"] == "starter-foundations"


def test_onboarding_flow_routes_household_manager_to_health():
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_learning_state()
    reset_goals_state()
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
    payload = complete.json()
    assert payload["persona_segment"] == "household_manager"
    assert payload["primary_route"] == "financial_health"


def test_onboarding_flow_routes_beginner_investor_to_guided_investing():
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_learning_state()
    reset_goals_state()
    reset_admin_cms_state()
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
    payload = complete.json()
    assert payload["persona_segment"] == "beginner_investor"
    assert payload["primary_route"] == "guided_investing"
    assert payload["guided_investing_eligible"] is True


def test_onboarding_flow_routes_advanced_to_insights_and_pro():
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_learning_state()
    reset_goals_state()
    reset_admin_cms_state()
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
    payload = complete.json()
    assert payload["persona_segment"] == "advanced_pro"
    assert payload["primary_route"] == "insights"
    assert payload["pro_eligible"] is True


def test_home_is_enriched_with_financial_health_snapshot_after_assessment():
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_learning_state()
    reset_goals_state()
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

    assessment = client.post(
        "/api/v1/public/financial-health/assessment",
        json={
            "session_id": session_id,
            "monthly_income_range": "low",
            "income_stability_level": "unstable",
            "expense_discipline_level": "no_tracking",
            "emergency_fund_months_band": "none",
            "monthly_debt_payment_ratio_band": "gt_50pct",
            "savings_rate_band": "none",
            "liquidity_stress_level": "frequent",
            "has_basic_insurance": False,
            "has_high_interest_debt": True,
            "wants_to_start_investing": True,
        },
    )
    assert assessment.status_code == 200

    home = client.get(f"/api/v1/public/home/{session_id}")
    assert home.status_code == 200
    payload = home.json()
    assert payload["health_snapshot"]["health_score"] >= 0
    assert payload["guided_investing_eligible"] is False
    assert payload["next_best_action_type"] == "start_emergency_fund_goal"
    health_block = next(block for block in payload["blocks"] if block["block_id"] == "health_snapshot")
    assert "Điểm hiện tại" in health_block["description"]


def test_home_is_enriched_with_goal_snapshot_after_goal_creation():
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_learning_state()
    reset_goals_state()
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

    created = client.post(
        "/api/v1/public/goals",
        json={
            "session_id": session_id,
            "goal_type": "emergency_fund",
            "goal_name": "Quy du phong gia dinh",
            "deadline": "2027-02-28",
            "target_amount": 24000000,
            "current_amount": 4000000,
            "priority": "high",
            "currency": "VND",
            "base_currency": "VND",
            "confidence_level": "estimated",
        },
    )
    assert created.status_code == 200

    home = client.get(f"/api/v1/public/home/{session_id}")
    assert home.status_code == 200
    payload = home.json()
    assert payload["goal_snapshot"]["goal_name"] == "Quy du phong gia dinh"
    assert payload["goal_snapshot"]["gap_amount"] > 0
    assert payload["goal_snapshot"]["reminder_status"] in {"on_track", "due_soon", "off_track"}
    assert payload["next_best_action_type"] in {"review_goal_progress", "stabilize_goal_plan"}
    goal_block = next(block for block in payload["blocks"] if block["block_id"] == "goals_snapshot")
    assert "Quy du phong gia dinh" in goal_block["description"]


def test_home_uses_published_nudge_template_from_content_ops(monkeypatch):
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_learning_state()
    reset_goals_state()
    reset_admin_cms_state()
    monkeypatch.setenv("ADMIN_CONTENT_OPS_KEY", "content-ops-test")
    client = TestClient(app)

    draft = client.put(
        "/admin/cms/content/nudge_template/new",
        headers=_content_ops_headers("editor"),
        json={
            "slug": "starter-home-continue-learning",
            "title": "Hoc tiep theo pace nhe",
            "locale": "vi-VN",
            "owner_team": "growth",
            "risk_category": "education",
            "payload": {
                "surface": "home",
                "trigger_type": "continue_learning_path",
                "persona_tags": ["starter"],
                "title_template": "Bước nhỏ tiếp theo",
                "message_template": "Bạn chưa cần làm nhiều việc cùng lúc. Hãy học tiếp một bài ngắn rồi quay lại Home.",
                "cta_label": "Mở bài học tiếp theo",
                "cta_path_template": "/learn",
            },
            "change_summary": "starter home nudge",
        },
    )
    assert draft.status_code == 200
    content_id = draft.json()["content_id"]
    assert client.post(
        f"/admin/cms/content/{content_id}/submit-review",
        headers=_content_ops_headers("editor"),
        json={"comments": "ready"},
    ).status_code == 200
    assert client.post(
        f"/admin/cms/content/{content_id}/approve",
        headers=_content_ops_headers("reviewer"),
        json={"comments": "clear"},
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
                {"question_key": "primary_goal", "answer_value": "understand_finance_basics"},
                {"question_key": "knowledge_level", "answer_value": "beginner"},
                {"question_key": "primary_interest", "answer_value": "basics"},
                {"question_key": "current_state", "answer_value": "no_clear_financial_system"},
                {"question_key": "risk_tolerance_prelim", "answer_value": "very_cautious"},
            ],
        },
    )
    assert complete.status_code == 200

    home = client.get(f"/api/v1/public/home/{session_id}")
    assert home.status_code == 200
    payload = home.json()
    assert payload["trust_message"] == "Bạn chưa cần làm nhiều việc cùng lúc. Hãy học tiếp một bài ngắn rồi quay lại Home."
    next_block = next(block for block in payload["blocks"] if block["block_id"] == "next_best_action")
    assert next_block["title"] == "Bước nhỏ tiếp theo"
    assert next_block["cta_label"] == "Mở bài học tiếp theo"
