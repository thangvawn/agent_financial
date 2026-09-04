from __future__ import annotations

import time
import pytest

from risk_dashboard.modules.learning.agent_tools import (
    LearningGetContextTool,
    LearningGetProgressTool,
    LearningGetQuizItemTool,
    LearningGradeCheckpointTool,
    LearningRecommendNextTool,
    LearningUpdateProgressTool,
    get_learning_tool_manifests,
)
from risk_dashboard.modules.learning.infrastructure.catalog_reader import SqliteLearningCatalog
from risk_dashboard.modules.learning.infrastructure.repositories.sqlite import reset_learning_state
from risk_dashboard.modules.learning.schemas.agent_tools import (
    GetContextInput,
    GetProgressInput,
    GetQuizItemInput,
    GradeCheckpointInput,
    RecommendNextInput,
    UpdateProgressInput,
)
from risk_dashboard.platform.database import open_app_state_db
from risk_dashboard.platform.database.migrate import apply_migrations


@pytest.fixture(autouse=True)
def setup_db():
    reset_learning_state()
    with open_app_state_db() as conn:
        apply_migrations(conn)


def test_manifest_registration() -> None:
    manifests = get_learning_tool_manifests()
    assert len(manifests) == 6
    tool_ids = {m.tool_id for m in manifests}
    expected_ids = {
        "learning.get_context",
        "learning.get_progress",
        "learning.get_quiz_item",
        "learning.grade_checkpoint",
        "learning.update_progress",
        "learning.recommend_next",
    }
    assert tool_ids == expected_ids


def test_get_context_tool_execution_and_latency() -> None:
    tool = LearningGetContextTool()
    start_time = time.perf_counter()
    res = tool.execute(GetContextInput(lesson_id="money-basics-101"))
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    assert elapsed_ms < 200  # Latency budget < 200ms
    assert res.lesson_id == "money-basics-101"
    assert res.canonical_content
    assert res.sources
    assert res.sources[0].content_version == "1.0.0"
    assert res.publication_status == "published"


def test_get_progress_tool_account_isolation() -> None:
    tool = LearningGetProgressTool()
    account_a = "user_account_a"
    account_b = "user_account_b"

    res_a = tool.execute(GetProgressInput(path_id="starter-foundations"), account_id=account_a)
    assert res_a.path_id == "starter-foundations"
    assert res_a.completion_pct == 0
    assert len(res_a.items) > 0

    res_b = tool.execute(GetProgressInput(path_id="starter-foundations"), account_id=account_b)
    assert res_b.completion_pct == 0


def test_checkpoint_grade_and_update_progress_full_flow() -> None:
    account_id = "test_learner_01"
    quiz_tool = LearningGetQuizItemTool()
    grade_tool = LearningGradeCheckpointTool()
    update_tool = LearningUpdateProgressTool()

    # 1. Get quiz item
    quiz_out = quiz_tool.execute(
        GetQuizItemInput(lesson_id="money-basics-101"),
        account_id=account_id,
    )
    assert quiz_out.checkpoint_id.startswith("cp_")
    assert quiz_out.lesson_id == "money-basics-101"
    assert quiz_out.prompt
    assert len(quiz_out.options) > 0

    # 2. Grade checkpoint with WRONG answer
    wrong_grade = grade_tool.execute(
        GradeCheckpointInput(checkpoint_id=quiz_out.checkpoint_id, response="A definitely wrong option"),
        account_id=account_id,
    )
    assert not wrong_grade.passed
    assert wrong_grade.score == 0
    assert wrong_grade.misconceptions

    # Cannot update progress with failed verified event
    with pytest.raises(ValueError, match="Cannot update progress"):
        update_tool.execute(
            UpdateProgressInput(
                verified_event_id=wrong_grade.verified_event_id,
                idempotency_key="idemp_fail",
                confirmation_id="conf_1",
            ),
            account_id=account_id,
        )

    # 3. Grade checkpoint with CORRECT answer dynamically retrieved from catalog
    catalog = SqliteLearningCatalog()
    lesson = catalog.get_lesson(lesson_id="money-basics-101")
    matching_q = next((q for q in lesson.quiz_questions if q.prompt == quiz_out.prompt), lesson.quiz_questions[0])
    correct_option = matching_q.correct_answer

    passed_grade = grade_tool.execute(
        GradeCheckpointInput(checkpoint_id=quiz_out.checkpoint_id, response=correct_option),
        account_id=account_id,
    )
    assert passed_grade.passed
    assert passed_grade.score == 100
    assert not passed_grade.misconceptions
    assert passed_grade.verified_event_id.startswith("ev_")

    # 4. Confirmed update progress with idempotency
    update_out_1 = update_tool.execute(
        UpdateProgressInput(
            verified_event_id=passed_grade.verified_event_id,
            idempotency_key="idemp_success_001",
            confirmation_id="conf_verified_001",
        ),
        account_id=account_id,
    )
    assert update_out_1.status == "completed"
    assert update_out_1.quiz_score == 100
    assert update_out_1.receipt_id.startswith("rcpt_")

    # Duplicate call with same idempotency key returns same receipt without error
    update_out_2 = update_tool.execute(
        UpdateProgressInput(
            verified_event_id=passed_grade.verified_event_id,
            idempotency_key="idemp_success_001",
            confirmation_id="conf_verified_001",
        ),
        account_id=account_id,
    )
    assert update_out_2.receipt_id == update_out_1.receipt_id
    assert update_out_2.status == update_out_1.status

    # 5. Check progress updated
    progress_tool = LearningGetProgressTool()
    prog = progress_tool.execute(GetProgressInput(path_id="starter-foundations"), account_id=account_id)
    assert prog.completion_pct > 0
    completed_items = [it for it in prog.items if it.status == "completed"]
    assert len(completed_items) >= 1
    assert completed_items[0].lesson_id == "money-basics-101"


def test_cross_account_checkpoint_rejection() -> None:
    quiz_tool = LearningGetQuizItemTool()
    grade_tool = LearningGradeCheckpointTool()

    quiz_out = quiz_tool.execute(
        GetQuizItemInput(lesson_id="money-basics-101"),
        account_id="account_owner",
    )

    with pytest.raises(PermissionError, match="does not belong"):
        grade_tool.execute(
            GradeCheckpointInput(checkpoint_id=quiz_out.checkpoint_id, response="Some answer"),
            account_id="account_intruder",
        )


def test_recommend_next_tool() -> None:
    tool = LearningRecommendNextTool()
    account_id = "user_recommend_01"

    rec_out = tool.execute(
        RecommendNextInput(path_id="starter-foundations", limit=2),
        account_id=account_id,
    )
    assert rec_out.path_id == "starter-foundations"
    assert len(rec_out.items) <= 2
    assert rec_out.items[0].rank == 1
    assert rec_out.items[0].lesson_id
    assert rec_out.items[0].rationale
