from __future__ import annotations

import pytest

from risk_dashboard.modules.admin_cms.domain.entities import CmsContentItem, CmsContentVersion, utc_now_iso
from risk_dashboard.modules.admin_cms.infrastructure.repositories.sqlite import SqliteAdminCmsRepository
from risk_dashboard.modules.learning.application.checkpoint_service import LearningCheckpointService
from risk_dashboard.modules.learning.application.memory_hooks import LearningMemoryGovernor
from risk_dashboard.modules.learning.domain.entities import VerifiedEventRecord
from risk_dashboard.modules.learning.infrastructure.catalog_reader import SqliteLearningCatalog
from risk_dashboard.modules.learning.infrastructure.repositories.sqlite import reset_learning_state
from risk_dashboard.platform.database import open_app_state_db
from risk_dashboard.platform.database.migrate import apply_migrations


@pytest.fixture(autouse=True)
def setup_db():
    reset_learning_state()
    with open_app_state_db() as conn:
        apply_migrations(conn)


def _seed_lesson(cms_repo: SqliteAdminCmsRepository, slug: str, questions: list[dict]) -> None:
    now = utc_now_iso()
    cms_repo.save_item(
        CmsContentItem(
            content_id=f"seed_{slug}",
            content_type="lesson",
            slug=slug,
            title=f"Lesson {slug}",
            locale="vi-VN",
            owner_team="education",
            risk_category="education",
            workflow_state="published",
            current_version=1,
            published_version=1,
            created_by="test",
            updated_by="test",
            created_at=now,
            updated_at=now,
        )
    )
    cms_repo.save_version(
        CmsContentVersion(
            version_id=f"seed_{slug}_v1",
            content_id=f"seed_{slug}",
            version_number=1,
            payload={
                "lesson_id": slug,
                "title": f"Lesson {slug}",
                "summary": "Summary",
                "tier": "financial_basics",
                "content_type": "micro_lesson",
                "estimated_minutes": 3,
                "body": ["Body"],
                "glossary": [],
                "quiz_questions": questions,
                "status": "published",
            },
            status="published",
            origin="test",
            change_summary="seed",
            created_by="test",
            reviewed_by="test",
            published_by="test",
            created_at=now,
            published_at=now,
        )
    )


def _make_event(account_id: str, score: int) -> VerifiedEventRecord:
    return VerifiedEventRecord(
        event_id=f"ev_{account_id}_{score}",
        account_id=account_id,
        checkpoint_id=f"cp_{score}",
        lesson_id="money-basics-101",
        score=score,
        passed=score >= 50,
        rubric_evidence=(f"Score {score}",),
        misconceptions=(),
        created_at="2026-09-12T10:00:00Z",
    )


def test_01_checkpoint_pool_random_selection() -> None:
    repo = SqliteAdminCmsRepository()
    questions = [
        {"question_id": f"q_{i}", "prompt": f"Prompt {i}?", "options": ["A", "B"], "correct_answer": "A"}
        for i in range(1, 6)
    ]
    _seed_lesson(repo, "pool-lesson", questions)
    service = LearningCheckpointService(catalog=SqliteLearningCatalog(content_ops_repo=repo))
    prompts = {
        service.create_checkpoint(account_id="user_1", lesson_id="pool-lesson").prompt
        for _ in range(20)
    }
    assert len(prompts) > 1


def test_02_checkpoint_pool_zero_answer_leakage() -> None:
    repo = SqliteAdminCmsRepository()
    questions = [{"question_id": "q_leak", "prompt": "P?", "options": ["A"], "correct_answer": "SECRET"}]
    _seed_lesson(repo, "leak-lesson", questions)
    service = LearningCheckpointService(catalog=SqliteLearningCatalog(content_ops_repo=repo))
    cp_dict = service.create_checkpoint(account_id="user_1", lesson_id="leak-lesson").model_dump()
    assert "correct_answer" not in cp_dict and "explanation" not in cp_dict and "answer_key" not in cp_dict


def test_03_checkpoint_pool_single_question_fallback() -> None:
    repo = SqliteAdminCmsRepository()
    _seed_lesson(repo, "single-q", [{"question_id": "q1", "prompt": "P1?", "options": ["A"], "correct_answer": "A"}])
    service = LearningCheckpointService(catalog=SqliteLearningCatalog(content_ops_repo=repo))
    cp = service.create_checkpoint(account_id="user_1", lesson_id="single-q")
    assert cp.prompt == "P1?"


def test_04_checkpoint_pool_boundary_ten_questions() -> None:
    repo = SqliteAdminCmsRepository()
    questions = [
        {"question_id": f"q_{i}", "prompt": f"Pool Q {i}?", "options": ["A"], "correct_answer": "A"}
        for i in range(1, 11)
    ]
    _seed_lesson(repo, "pool-ten", questions)
    service = LearningCheckpointService(catalog=SqliteLearningCatalog(content_ops_repo=repo))
    cp = service.create_checkpoint(account_id="user_1", lesson_id="pool-ten")
    assert cp.prompt.startswith("Pool Q")


def test_05_mastery_threshold_retail_75_passes() -> None:
    ev75 = _make_event("retail_user", 75)
    prop = LearningMemoryGovernor.propose_mastery(verified_event=ev75, tier="community", role="retail")
    assert prop is not None and prop.score == 75

    ev74 = _make_event("retail_user", 74)
    assert LearningMemoryGovernor.propose_mastery(verified_event=ev74, tier="community", role="retail") is None


def test_06_mastery_threshold_pro_75_and_80_rejected() -> None:
    ev75 = _make_event("pro_user", 75)
    assert LearningMemoryGovernor.propose_mastery(verified_event=ev75, tier="pro", role="institutional") is None

    ev80 = _make_event("pro_user", 80)
    assert LearningMemoryGovernor.propose_mastery(verified_event=ev80, tier="pro", role="institutional") is None


def test_07_mastery_threshold_pro_85_passes() -> None:
    ev85 = _make_event("pro_user", 85)
    prop = LearningMemoryGovernor.propose_mastery(verified_event=ev85, tier="pro", role="institutional")
    assert prop is not None and prop.score == 85


def test_08_mastery_threshold_default_80() -> None:
    ev79 = _make_event("def_user", 79)
    assert LearningMemoryGovernor.propose_mastery(verified_event=ev79, tier="standard") is None

    ev80 = _make_event("def_user", 80)
    prop = LearningMemoryGovernor.propose_mastery(verified_event=ev80, tier="standard")
    assert prop is not None and prop.score == 80
