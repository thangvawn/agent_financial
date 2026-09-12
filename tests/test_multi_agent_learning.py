from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.learning.infrastructure.repositories.sqlite import reset_learning_state
from risk_dashboard.platform.database import open_app_state_db
from risk_dashboard.platform.database.migrate import apply_migrations


@pytest.fixture(autouse=True)
def setup_db():
    reset_learning_state()
    with open_app_state_db() as conn:
        apply_migrations(conn)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_api_get_checkpoint_item(client: TestClient) -> None:
    """GET /api/v1/public/learning/checkpoint returns 200 with item details and zero answer leakage."""
    res = client.get("/api/v1/public/learning/checkpoint?lesson_id=money-basics-101")
    assert res.status_code == 200
    data = res.json()
    assert "checkpoint_id" in data
    assert "prompt" in data
    assert "options" in data
    assert "correct_answer" not in data
    assert "explanation" not in data
    assert "answer_key" not in data


def test_api_grade_checkpoint_answer(client: TestClient) -> None:
    """POST /api/v1/public/learning/checkpoint/grade returns 200 with grading outcome and verified_event_id."""
    cp_res = client.get("/api/v1/public/learning/checkpoint?lesson_id=money-basics-101")
    assert cp_res.status_code == 200
    checkpoint_id = cp_res.json()["checkpoint_id"]

    res = client.post(
        "/api/v1/public/learning/checkpoint/grade",
        json={
            "checkpoint_id": checkpoint_id,
            "response": "A",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "passed" in data
    assert "verified_event_id" in data


def test_api_complete_checkpoint(client: TestClient) -> None:
    """POST /api/v1/public/learning/checkpoint/complete returns 200 with receipt and progress update."""
    cp_res = client.get("/api/v1/public/learning/checkpoint?lesson_id=money-basics-101")
    assert cp_res.status_code == 200
    cp_data = cp_res.json()
    checkpoint_id = cp_data["checkpoint_id"]
    correct_option = cp_data["options"][0]

    grade_res = client.post(
        "/api/v1/public/learning/checkpoint/grade",
        json={
            "checkpoint_id": checkpoint_id,
            "response": correct_option,
        },
    )
    assert grade_res.status_code == 200
    verified_event_id = grade_res.json()["verified_event_id"]

    res = client.post(
        "/api/v1/public/learning/checkpoint/complete",
        json={
            "verified_event_id": verified_event_id,
            "idempotency_key": "idemp_test_01",
            "confirmation_id": "conf_test_01",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "receipt_id" in data or "receipt" in data
    assert "status" in data or "progress" in data


def test_gold_set_runs_through_multi_agent() -> None:
    """Run 100 gold-set test cases through Multi-Agent / Agentic Core E2E runner."""
    from risk_dashboard.modules.learning.evals.multi_agent_runner import LearningMultiAgentEvalRunner

    runner = LearningMultiAgentEvalRunner()
    summary = runner.run_suite()
    assert summary.total_cases >= 100
    assert summary.passed_cases >= 98
    assert summary.status == "PASSED"

