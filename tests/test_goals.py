from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
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


def test_create_goal_and_list_it_for_session():
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_learning_state()
    reset_goals_state()
    client = TestClient(app)
    session_id = client.post("/api/v1/public/onboarding/start").json()["session_id"]

    response = client.post(
        "/api/v1/public/goals",
        json={
            "session_id": session_id,
            "goal_type": "emergency_fund",
            "goal_name": "Quy du phong 1 thang",
            "deadline": "2027-01-31",
            "target_amount": 20000000,
            "current_amount": 2000000,
            "priority": "high",
            "currency": "VND",
            "base_currency": "VND",
            "confidence_level": "estimated",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["goal_type"] == "emergency_fund"
    assert payload["monthly_contribution_needed"] > 0
    assert payload["actions"]
    assert payload["reminder_status"] in {"on_track", "due_soon", "off_track", "completed"}

    listed = client.get(f"/api/v1/public/goals?session_id={session_id}")
    assert listed.status_code == 200
    items = listed.json()
    assert len(items) == 1
    assert items[0]["goal_name"] == "Quy du phong 1 thang"
    assert items[0]["reminder_status"] in {"on_track", "due_soon", "off_track", "completed"}


def test_goal_planner_and_checkin_flow():
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_learning_state()
    reset_goals_state()
    client = TestClient(app)
    session_id = "session-goal-002"

    health = client.post(
        "/api/v1/public/financial-health/assessment",
        json={
            "session_id": session_id,
            "monthly_income_range": "mid",
            "income_stability_level": "mostly_stable",
            "expense_discipline_level": "mostly_disciplined",
            "emergency_fund_months_band": "1_to_3m",
            "monthly_debt_payment_ratio_band": "10_to_30pct",
            "savings_rate_band": "10_to_20pct",
            "liquidity_stress_level": "rare",
            "has_basic_insurance": True,
            "has_high_interest_debt": False,
            "wants_to_start_investing": True,
        },
    )
    assert health.status_code == 200

    created = client.post(
        "/api/v1/public/goals",
        json={
            "session_id": session_id,
            "goal_type": "home_purchase",
            "goal_name": "Dat coc mua nha",
            "deadline": "2027-12-31",
            "target_amount": 300000000,
            "current_amount": 30000000,
            "priority": "high",
            "currency": "VND",
            "base_currency": "VND",
            "confidence_level": "rough",
        },
    )
    assert created.status_code == 200
    goal_id = created.json()["goal_id"]

    planner = client.post(f"/api/v1/public/goals/{goal_id}/planner")
    assert planner.status_code == 200
    planner_payload = planner.json()
    assert planner_payload["summary"]
    assert planner_payload["trade_offs"]

    checked_in = client.post(
        f"/api/v1/public/goals/{goal_id}/check-in",
        json={"current_amount": 50000000, "note": "Tang them tien tiet kiem"},
    )
    assert checked_in.status_code == 200
    checked_payload = checked_in.json()
    assert checked_payload["current_amount"] == 50000000
    assert checked_payload["gap_amount"] < created.json()["gap_amount"]
    assert checked_payload["reminder_status"] in {"on_track", "due_soon", "off_track", "completed"}
