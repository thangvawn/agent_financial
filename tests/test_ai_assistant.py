from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.financial_health.infrastructure.repositories.sqlite import reset_financial_health_state
from risk_dashboard.modules.goals.infrastructure.repositories.sqlite import reset_goals_state
from risk_dashboard.modules.home_onboarding.infrastructure.repositories.sqlite import reset_home_onboarding_state
from risk_dashboard.modules.learning.infrastructure.repositories.sqlite import reset_learning_state
from risk_dashboard.modules.pro_lab.infrastructure.repositories.sqlite import reset_pro_lab_state
from risk_dashboard.platform.database import open_app_state_db
from risk_dashboard.modules.ai_assistant.evaluation.golden_cases import GOLDEN_ASSISTANT_CASES


def test_ai_assistant_public_roles_and_feedback(monkeypatch):
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_goals_state()
    reset_learning_state()
    client = TestClient(app)

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

    learning_home = client.get(f"/api/v1/public/learning/home?session_id={session_id}")
    lesson_id = learning_home.json()["next_lesson_id"]

    tutor = client.post(
        "/api/v1/public/ai-assistant/respond",
        json={
            "session_id": session_id,
            "surface": "learning",
            "prompt": "Giai thich bai nay nhu cho nguoi moi.",
            "lesson_id": lesson_id,
        },
    )
    assert tutor.status_code == 200
    tutor_payload = tutor.json()
    assert tutor_payload["role"] == "tutor"
    assert tutor_payload["allowed"] is True
    assert tutor_payload["check_question"]

    feedback = client.post(
        "/api/v1/public/ai-assistant/feedback",
        json={
            "conversation_id": tutor_payload["conversation_id"],
            "message_id": tutor_payload["message_id"],
            "rating": 5,
            "reason_code": "helpful",
        },
    )
    assert feedback.status_code == 200
    assert feedback.json()["saved"] is True

    client.post(
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
    coach = client.post(
        "/api/v1/public/ai-assistant/respond",
        json={
            "session_id": session_id,
            "surface": "financial_health",
            "prompt": "",
            "role_hint": "coach",
            "focus": "investment_readiness",
        },
    )
    assert coach.status_code == 200
    assert coach.json()["role"] == "coach"
    assert coach.json()["cta_path"] == "/financial-health"

    analyst = client.post(
        "/api/v1/public/ai-assistant/respond",
        json={
            "session_id": session_id,
            "surface": "guided_investing",
            "prompt": "Ma nao nen mua ngay bay gio?",
        },
    )
    assert analyst.status_code == 200
    assert analyst.json()["role"] == "analyst"
    assert analyst.json()["allowed"] is False

    with open_app_state_db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM ai_conversation_sessions").fetchone()[0] >= 3
        assert conn.execute("SELECT COUNT(*) FROM ai_feedback").fetchone()[0] >= 1


def test_ai_assistant_pro_role_with_scope(monkeypatch):
    reset_home_onboarding_state()
    reset_pro_lab_state()
    monkeypatch.setenv("PRO_LAB_KEY", "pro-lab-test")
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
                {"question_key": "risk_tolerance_prelim", "answer_value": "moderate"},
            ],
        },
    )
    assert complete.status_code == 200
    assert complete.json()["pro_eligible"] is True

    access = client.post("/api/v1/public/pro-lab/access-token", json={"session_id": session_id})
    assert access.status_code == 200
    access_token = access.json()["access_token"]

    client.post(
        "/api/v1/pro/pro-lab/blueprints",
        headers={"X-Access-Token": access_token},
        json={
            "user_id": session_id,
            "name": "VN Quality Rotation",
            "objective": "Tao workspace premium de benchmark va stress-test strategy blueprint co caveat ro rang.",
            "asset_universe": ["FPT", "VCB", "MWG"],
            "benchmark": "VNINDEX",
            "rebalance_frequency": "monthly",
            "risk_constraints": "Max concentration 35%, no single-theme overload",
            "assumptions_note": "Khong dung de phat tin hieu cong khai.",
        },
    )

    response = client.post(
        "/api/v1/pro/ai-assistant/respond",
        headers={"X-Access-Token": access_token},
        json={
            "session_id": session_id,
            "surface": "pro_lab",
            "prompt": "Tom tat workspace va caveat chinh cho toi.",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["role"] == "pro_assistant"
    assert payload["allowed"] is True
    assert payload["cta_path"] == "/pro-lab"


def test_ai_assistant_structured_contract_and_golden_cases():
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_goals_state()
    reset_learning_state()
    client = TestClient(app)

    session_id = client.post("/api/v1/public/onboarding/start").json()["session_id"]
    complete = client.post(
        "/api/v1/public/onboarding/complete",
        json={
            "session_id": session_id,
            "answers": [
                {"question_key": "primary_goal", "answer_value": "learn_investing_safely"},
                {"question_key": "knowledge_level", "answer_value": "basic"},
                {"question_key": "primary_interest", "answer_value": "markets"},
                {"question_key": "current_state", "answer_value": "already_saving_wants_to_invest"},
                {"question_key": "risk_tolerance_prelim", "answer_value": "moderate"},
            ],
        },
    )
    assert complete.status_code == 200

    for case in GOLDEN_ASSISTANT_CASES:
        response = client.post(
            "/api/v1/public/ai-assistant/respond",
            json={
                "session_id": session_id,
                "surface": case["surface"],
                "prompt": case["prompt"],
            },
        )
        assert response.status_code == 200, case["name"]
        payload = response.json()
        assert payload["role"] == case["expected_role"], case["name"]
        assert payload["intent"] == case["expected_intent"], case["name"]
        assert payload["allowed"] is case["must_allow"], case["name"]
        assert payload["mode_used"] == payload["role"]
        assert payload["confidence_label"]
        assert payload["data_freshness"]
        assert isinstance(payload["warnings"], list)
        assert isinstance(payload["next_actions"], list)
        assert isinstance(payload["sources"], list)
        assert payload["response_blocks"]


def test_ai_assistant_unknown_guided_session_degrades_safely():
    reset_home_onboarding_state()
    client = TestClient(app)

    response = client.post(
        "/api/v1/public/ai-assistant/respond",
        json={
            "session_id": "missing-session",
            "surface": "guided_investing",
            "prompt": "Giai thich market risk hien tai cho nguoi moi.",
            "role_hint": "analyst",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["role"] == "analyst"
    assert payload["route_decision"] == "explained_guest_market_context"
    assert payload["allowed"] is True
    assert payload["cta_path"] == "/onboarding"


def test_ai_assistant_greeting_does_not_become_coach_nudge():
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_goals_state()
    reset_learning_state()
    client = TestClient(app)

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

    response = client.post(
        "/api/v1/public/ai-assistant/respond",
        json={
            "session_id": session_id,
            "surface": "home",
            "prompt": "hi",
            "role_hint": "coach",
            "trigger": "floating_coach",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "smalltalk_greeting"
    assert payload["route_decision"] == "greeted_user"
    assert payload["cta_path"] == ""
    assert "bước nhỏ" not in payload["summary"].lower()


def test_ai_assistant_voice_synthesize_fallback_without_key(monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    client = TestClient(app)

    response = client.post(
        "/api/v1/public/ai-assistant/voice/synthesize",
        json={"text": "Xin chao, toi muon xem tom tat rui ro hom nay."},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "elevenlabs"
    assert payload["enabled"] is False
    assert payload["audio_base64"] is None
    assert payload["fallback_reason"]
