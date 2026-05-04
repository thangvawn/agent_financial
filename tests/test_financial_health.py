from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.financial_health.infrastructure.repositories.sqlite import (
    reset_financial_health_state,
)


def test_financial_health_assessment_returns_explainable_snapshot():
    reset_financial_health_state()
    client = TestClient(app)
    session_id = "session-fin-health-001"
    response = client.post(
        "/api/v1/public/financial-health/assessment",
        json={
            "session_id": session_id,
            "monthly_income_range": "mid",
            "income_stability_level": "stable",
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
    assert response.status_code == 200
    payload = response.json()
    assert 0 <= payload["health_score"] <= 100
    assert len(payload["subscores"]) == 8
    assert "transparency_note" in payload
    assert "compliance_note" in payload


def test_financial_health_risky_profile_sets_flags_and_blocks_guided_investing():
    reset_financial_health_state()
    client = TestClient(app)
    session_id = "session-fin-health-002"
    response = client.post(
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
    assert response.status_code == 200
    payload = response.json()
    assert payload["guided_investing_eligible"] is False
    assert payload["flags"]
    assert any(flag["code"] == "low_emergency_buffer" for flag in payload["flags"])
    assert any(action["code"] == "start_emergency_fund_goal" for action in payload["actions"])


def test_financial_health_coach_explains_snapshot():
    reset_financial_health_state()
    client = TestClient(app)
    session_id = "session-fin-health-003"
    client.post(
        "/api/v1/public/financial-health/assessment",
        json={
            "session_id": session_id,
            "monthly_income_range": "mid",
            "income_stability_level": "variable",
            "expense_discipline_level": "inconsistent",
            "emergency_fund_months_band": "lt_1m",
            "monthly_debt_payment_ratio_band": "30_to_50pct",
            "savings_rate_band": "lt_10pct",
            "liquidity_stress_level": "sometimes",
            "has_basic_insurance": False,
            "has_high_interest_debt": True,
            "wants_to_start_investing": False,
        },
    )
    response = client.post(
        f"/api/v1/public/financial-health/coach?session_id={session_id}&focus=investment_readiness"
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]
    assert payload["explanation"]
    assert payload["next_small_actions"]
