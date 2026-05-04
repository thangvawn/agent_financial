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
from risk_dashboard.modules.learning.domain.entities import LearningCmsDocument, utc_now_iso
from risk_dashboard.modules.learning.infrastructure.repositories.sqlite import SqliteLearningCmsRepository
from risk_dashboard.modules.learning.infrastructure.repositories.sqlite import (
    reset_learning_state,
)


def _content_ops_headers(role: str) -> dict[str, str]:
    return {
        "X-Admin-Content-Ops-Key": "content-ops-test",
        "X-Content-Ops-Role": role,
    }


def test_learning_home_lesson_quiz_and_context_flow():
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_goals_state()
    reset_learning_state()
    reset_admin_cms_state()
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

    home = client.get(f"/api/v1/public/learning/home?session_id={session_id}")
    assert home.status_code == 200
    home_payload = home.json()
    assert home_payload["path_id"] == "starter-foundations"
    lesson_id = home_payload["next_lesson_id"]

    lesson = client.get(f"/api/v1/public/learning/lessons/{lesson_id}?session_id={session_id}")
    assert lesson.status_code == 200
    lesson_payload = lesson.json()
    assert lesson_payload["lesson_id"] == lesson_id
    assert lesson_payload["quiz_questions"]

    first_question = lesson_payload["quiz_questions"][0]
    quiz = client.post(
        f"/api/v1/public/learning/lessons/{lesson_id}/quiz",
        json={"session_id": session_id, "answers": {first_question["question_id"]: first_question["options"][0]}},
    )
    assert quiz.status_code == 200
    quiz_payload = quiz.json()
    assert 0 <= quiz_payload["score"] <= 100
    assert quiz_payload["explanations"]

    completed = client.post(f"/api/v1/public/learning/lessons/{lesson_id}/complete?session_id={session_id}")
    assert completed.status_code == 200
    completed_payload = completed.json()
    assert completed_payload["progress_status"] == "completed"

    tutor = client.post(
        "/api/v1/public/learning/tutor",
        json={
            "session_id": session_id,
            "lesson_id": lesson_id,
            "question": "Tom tat bai nay cho toi nhu nguoi moi.",
            "knowledge_level": "beginner",
        },
    )
    assert tutor.status_code == 200
    tutor_payload = tutor.json()
    assert tutor_payload["summary"]
    assert tutor_payload["check_question"]

    coach = client.post(
        "/api/v1/public/learning/coach",
        json={"session_id": session_id, "trigger": "continue_path"},
    )
    assert coach.status_code == 200
    coach_payload = coach.json()
    assert coach_payload["title"]
    assert coach_payload["cta_path"] == "/learn"

    context = client.get("/api/v1/public/learning/context?trigger=drawdown")
    assert context.status_code == 200
    context_payload = context.json()
    assert context_payload["recommended_lesson_id"] == "drawdown-basics-101"


def test_learning_admin_cms_draft_and_publish_override_public_catalog():
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_goals_state()
    reset_learning_state()
    reset_admin_cms_state()
    client = TestClient(app)
    retired_paths = (
        "/admin/learning-cms",
        "/admin/learning-cms/status",
        "/admin/learning-cms/lessons",
        "/admin/learning-cms/lessons/money-basics-101",
        "/admin/learning-cms/courses",
        "/admin/learning-cms/paths/starter-foundations",
    )
    for path in retired_paths:
        response = client.get(path)
        assert response.status_code == 410
        assert "retire" in response.json()["detail"].lower()

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

    public_lesson_draft = client.get(f"/api/v1/public/learning/lessons/money-basics-101?session_id={session_id}")
    assert public_lesson_draft.status_code == 200
    assert public_lesson_draft.json()["lesson_id"] == "money-basics-101"


def test_content_ops_published_path_controls_learning_home_route(monkeypatch):
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_goals_state()
    reset_learning_state()
    reset_admin_cms_state()
    monkeypatch.setenv("ADMIN_CONTENT_OPS_KEY", "content-ops-test")
    client = TestClient(app)

    lesson = client.put(
        "/admin/cms/content/lesson/new",
        headers=_content_ops_headers("editor"),
        json={
            "slug": "ops-path-lesson",
            "title": "Ops path lesson",
            "locale": "vi-VN",
            "owner_team": "education",
            "risk_category": "education",
            "payload": {
                "title": "Ops path lesson",
                "summary": "Lesson duoc seed tu path moi.",
                "tier": "financial_basics",
                "content_type": "micro_lesson",
                "estimated_minutes": 4,
                "body": ["Noi dung cho path moi."],
                "quiz_questions": [],
            },
            "change_summary": "path lesson",
        },
    )
    assert lesson.status_code == 200
    lesson_content_id = lesson.json()["content_id"]
    assert client.post(f"/admin/cms/content/{lesson_content_id}/submit-review", headers=_content_ops_headers("editor"), json={}).status_code == 200
    assert client.post(f"/admin/cms/content/{lesson_content_id}/approve", headers=_content_ops_headers("reviewer"), json={}).status_code == 200
    assert client.post(f"/admin/cms/content/{lesson_content_id}/publish", headers=_content_ops_headers("admin"), json={}).status_code == 200

    path = client.put(
        "/admin/cms/content/path/new",
        headers=_content_ops_headers("editor"),
        json={
            "slug": "starter-foundations",
            "title": "Starter path tu Content Ops",
            "locale": "vi-VN",
            "owner_team": "education",
            "risk_category": "education",
            "payload": {
                "path_id": "starter-foundations",
                "title": "Starter path tu Content Ops",
                "persona_segment": "starter",
                "lesson_ids": ["ops-path-lesson"],
                "description": "Path starter duoc quan ly boi Content Ops.",
            },
            "change_summary": "path override",
        },
    )
    assert path.status_code == 200
    path_content_id = path.json()["content_id"]
    assert client.post(f"/admin/cms/content/{path_content_id}/submit-review", headers=_content_ops_headers("editor"), json={}).status_code == 200
    assert client.post(f"/admin/cms/content/{path_content_id}/approve", headers=_content_ops_headers("reviewer"), json={}).status_code == 200
    assert client.post(f"/admin/cms/content/{path_content_id}/publish", headers=_content_ops_headers("admin"), json={}).status_code == 200

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

    home = client.get(f"/api/v1/public/learning/home?session_id={session_id}")
    assert home.status_code == 200
    payload = home.json()
    assert payload["path_id"] == "starter-foundations"
    assert payload["path_label"] == "Starter path tu Content Ops"
    assert payload["next_lesson_id"] == "ops-path-lesson"


def test_content_ops_published_lesson_and_context_are_used_by_learning_runtime(monkeypatch):
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_goals_state()
    reset_learning_state()
    reset_admin_cms_state()
    monkeypatch.setenv("ADMIN_CONTENT_OPS_KEY", "content-ops-test")
    client = TestClient(app)

    glossary = client.put(
        "/admin/cms/content/glossary_term/new",
        headers=_content_ops_headers("editor"),
        json={
            "slug": "cash-flow-ops",
            "title": "Cash flow",
            "locale": "vi-VN",
            "owner_team": "education",
            "risk_category": "education",
            "payload": {
                "term": "Cash flow",
                "short_definition": "Dong tien duoc dinh nghia tu Content Ops.",
            },
            "change_summary": "glossary runtime test",
        },
    )
    assert glossary.status_code == 200
    glossary_id = glossary.json()["content_id"]
    assert client.post(
        f"/admin/cms/content/{glossary_id}/submit-review",
        headers=_content_ops_headers("editor"),
        json={"comments": "ready"},
    ).status_code == 200
    assert client.post(
        f"/admin/cms/content/{glossary_id}/approve",
        headers=_content_ops_headers("reviewer"),
        json={"comments": "clear"},
    ).status_code == 200
    assert client.post(
        f"/admin/cms/content/{glossary_id}/publish",
        headers=_content_ops_headers("admin"),
        json={"comments": "publish"},
    ).status_code == 200

    lesson = client.put(
        "/admin/cms/content/lesson/new",
        headers=_content_ops_headers("editor"),
        json={
            "slug": "ops-runtime-lesson",
            "title": "Lesson tu Content Ops",
            "locale": "vi-VN",
            "owner_team": "education",
            "risk_category": "education",
            "payload": {
                "title": "Lesson tu Content Ops",
                "summary": "Lesson public duoc cap boi Content Ops.",
                "tier": "financial_basics",
                "content_type": "micro_lesson",
                "estimated_minutes": 5,
                "body": ["Noi dung lesson runtime moi."],
                "glossary_refs": ["cash-flow-ops"],
                "quiz_questions": [
                    {
                        "question_id": "ops-q1",
                        "prompt": "Cash flow la gi?",
                        "options": ["Dong tien", "Chi so gia"],
                        "correct_answer": "Dong tien",
                        "explanation": "Cash flow la dong tien vao ra.",
                    }
                ],
            },
            "change_summary": "lesson runtime test",
        },
    )
    assert lesson.status_code == 200
    lesson_id = lesson.json()["content_id"]
    assert client.post(
        f"/admin/cms/content/{lesson_id}/submit-review",
        headers=_content_ops_headers("editor"),
        json={"comments": "ready"},
    ).status_code == 200
    assert client.post(
        f"/admin/cms/content/{lesson_id}/approve",
        headers=_content_ops_headers("reviewer"),
        json={"comments": "clear"},
    ).status_code == 200
    assert client.post(
        f"/admin/cms/content/{lesson_id}/publish",
        headers=_content_ops_headers("admin"),
        json={"comments": "publish"},
    ).status_code == 200

    explainer = client.put(
        "/admin/cms/content/contextual_explainer/new",
        headers=_content_ops_headers("editor"),
        json={
            "slug": "drawdown",
            "title": "Drawdown runtime explainer",
            "locale": "vi-VN",
            "owner_team": "education",
            "risk_category": "education",
            "payload": {
                "surface": "learning",
                "title": "Drawdown runtime explainer",
                "body": ["Context runtime tu Content Ops cho drawdown."],
                "linked_lesson_ids": ["ops-runtime-lesson"],
            },
            "change_summary": "context runtime test",
        },
    )
    assert explainer.status_code == 200
    explainer_id = explainer.json()["content_id"]
    assert client.post(
        f"/admin/cms/content/{explainer_id}/submit-review",
        headers=_content_ops_headers("editor"),
        json={"comments": "ready"},
    ).status_code == 200
    assert client.post(
        f"/admin/cms/content/{explainer_id}/approve",
        headers=_content_ops_headers("reviewer"),
        json={"comments": "clear"},
    ).status_code == 200
    assert client.post(
        f"/admin/cms/content/{explainer_id}/publish",
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

    public_lesson = client.get(f"/api/v1/public/learning/lessons/ops-runtime-lesson?session_id={session_id}")
    assert public_lesson.status_code == 200
    assert public_lesson.json()["title"] == "Lesson tu Content Ops"
    assert public_lesson.json()["glossary"][0]["definition"] == "Dong tien duoc dinh nghia tu Content Ops."

    context = client.get("/api/v1/public/learning/context?trigger=drawdown")
    assert context.status_code == 200
    assert context.json()["recommended_lesson_id"] == "ops-runtime-lesson"
    assert context.json()["reason"] == "Context runtime tu Content Ops cho drawdown."


def test_learning_runtime_ignores_legacy_learning_cms_published_override():
    reset_home_onboarding_state()
    reset_financial_health_state()
    reset_goals_state()
    reset_learning_state()
    reset_admin_cms_state()
    client = TestClient(app)

    repo = SqliteLearningCmsRepository()
    repo.save_document(
        LearningCmsDocument(
            doc_type="lesson",
            doc_id="money-basics-101",
            status="published",
            payload={
                "lesson_id": "money-basics-101",
                "title": "Legacy lesson phai bi bo qua",
                "summary": "Neu runtime con doc learning-cms cu thi test nay se vo.",
                "tier": "financial_basics",
                "content_type": "micro_lesson",
                "estimated_minutes": 2,
                "body": ["Legacy body."],
                "glossary": [],
                "quiz_questions": [],
                "next_lesson_id": "cashflow-basics-101",
            },
            updated_at=utc_now_iso(),
            published_at=utc_now_iso(),
        )
    )

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

    lesson = client.get(f"/api/v1/public/learning/lessons/money-basics-101?session_id={session_id}")
    assert lesson.status_code == 200
    assert lesson.json()["title"] != "Legacy lesson phai bi bo qua"
