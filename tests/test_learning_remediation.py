from __future__ import annotations

import asyncio
import pytest

from risk_dashboard.modules.agentic_core.application.tool_grants import resolve_grant
from risk_dashboard.modules.agentic_core.application.tool_registry import get_default_tool_registry
from risk_dashboard.modules.agentic_core.domain.tools import ToolGrant
from risk_dashboard.modules.agentic_core.infrastructure.domain_tools import LearningGetLessonContextTool
import risk_dashboard.modules.agentic_core.infrastructure.domain_tools as domain_tools
from risk_dashboard.modules.agentic_core.schemas.envelope import ExecutionBudget, TrustedExecutionEnvelope
from risk_dashboard.modules.auth.schemas.principal import ConsentSnapshot
from risk_dashboard.modules.learning.infrastructure.catalog_reader import SqliteLearningCatalog
from risk_dashboard.modules.learning.infrastructure.repositories.sqlite import (
    SqliteLearningHomeRepository,
    reset_learning_state,
)
from risk_dashboard.modules.learning.schemas.agent_tools import (
    GetQuizItemInput,
    GradeCheckpointInput,
    UpdateProgressInput,
)
from risk_dashboard.platform.database import open_app_state_db
from risk_dashboard.platform.database.migrate import apply_migrations


@pytest.fixture(autouse=True)
def setup_db():
    reset_learning_state()
    with open_app_state_db() as conn:
        apply_migrations(conn)


def test_tool_registry_contains_learning_tools():
    """GAP-1: ToolRegistry vắng bóng 6 tools Module 4 (Learning Engine)."""
    registry = get_default_tool_registry()
    learning_tool_ids = [
        "learning.get_context",
        "learning.get_progress",
        "learning.get_quiz_item",
        "learning.grade_checkpoint",
        "learning.update_progress",
        "learning.recommend_next",
    ]
    for tool_id in learning_tool_ids:
        manifest = registry.get(tool_id)
        assert manifest is not None, f"Tool '{tool_id}' is missing from get_default_tool_registry()"


def test_tool_grants_allow_learning_capabilities():
    """GAP-2: ToolGrants từ chối hoặc không cấp quyền cho capabilities learning mới."""
    envelope = TrustedExecutionEnvelope(
        run_id="run_learn_001",
        correlation_id="corr_learn_001",
        idempotency_key="idemp_learn_001",
        account_id="acc_test",
        scopes=("learning:all",),
        surface="learn_hub",
        allowed_capabilities=(
            "learn:content:read",
            "learn:progress:read",
            "learn:checkpoint:read",
            "learn:checkpoint:grade",
            "learn:recommendation:read",
        ),
        budget=ExecutionBudget(max_tool_calls=5),
        policy_version="1.0.0",
        model_policy_version="1.0.0",
        consent=ConsentSnapshot(memory=False, analytics=False, consented_at="2026-09-12T00:00:00Z", policy_version="1.0.0"),
        created_at="2026-09-12T00:00:00Z",
    )

    registry = get_default_tool_registry()
    manifest = registry.get("learning.get_context")
    assert manifest is not None, "Tool 'learning.get_context' must be registered in ToolRegistry"

    grant = resolve_grant(envelope, manifest)
    assert grant is not None, "resolve_grant must grant access for learn:content:read capability"
    assert grant.tool_id == "learning.get_context"


def test_learning_tools_execute_real_db_calls():
    """GAP-3: Learning tool adapter trong agentic_core trả mock stub tĩnh thay vì query DB thật."""
    tool = LearningGetLessonContextTool()
    grant = ToolGrant(
        grant_id="g_test_01",
        run_id="run_01",
        tool_id="learning.get_context",
        resource_id="lesson:money-basics-101",
        expires_at="2099-01-01T00:00:00Z",
    )
    res = asyncio.run(tool.execute(grant))

    # Adapter hiện tại trả hardcoded mock "Value at Risk" / "Market risk modeling"
    assert res.get("topic") != "Value at Risk", "Tool returned hardcoded mock stub 'Value at Risk' instead of querying real DB"
    assert res.get("tool_id") == "learning.get_context", f"Expected tool_id 'learning.get_context', got {res.get('tool_id')}"
    assert "Tiền tệ" in str(res) or "title" in res or "canonical_content" in res, "Expected real DB content for money-basics-101"


def test_checkpoint_token_generation_via_tool():
    """GAP-4: Tool checkpoint không được tích hợp vào agentic_core và phải sinh token không leak đáp án."""
    manifest = get_default_tool_registry().get("learning.get_quiz_item")
    assert manifest is not None, "Tool 'learning.get_quiz_item' is missing from ToolRegistry"

    tool_cls = getattr(domain_tools, "LearningGetQuizItemTool", None)
    assert tool_cls is not None, "LearningGetQuizItemTool must be available in agentic_core.infrastructure.domain_tools"

    quiz_tool = tool_cls()
    account_id = "test_learner_01"
    quiz_out = quiz_tool.execute(
        GetQuizItemInput(lesson_id="money-basics-101"),
        account_id=account_id,
    )
    assert quiz_out.checkpoint_id.startswith("cp_"), "Checkpoint token must start with 'cp_'"
    assert quiz_out.lesson_id == "money-basics-101"
    assert quiz_out.prompt
    assert len(quiz_out.options) > 0
    assert not hasattr(quiz_out, "correct_answer"), "GetQuizItemOutput must not leak correct_answer"
    assert "correct_answer" not in quiz_out.model_dump(), "GetQuizItemOutput serialized payload must not contain correct_answer"


def test_grade_checkpoint_rejects_cheating():
    """GAP-5: Tool grading checkpoint không được tích hợp vào agentic_core; sai đáp án không pass, đúng mới pass."""
    manifest_grade = get_default_tool_registry().get("learning.grade_checkpoint")
    assert manifest_grade is not None, "Tool 'learning.grade_checkpoint' is missing from ToolRegistry"

    quiz_tool_cls = getattr(domain_tools, "LearningGetQuizItemTool", None)
    grade_tool_cls = getattr(domain_tools, "LearningGradeCheckpointTool", None)
    assert quiz_tool_cls is not None, "LearningGetQuizItemTool must be available in agentic_core.infrastructure.domain_tools"
    assert grade_tool_cls is not None, "LearningGradeCheckpointTool must be available in agentic_core.infrastructure.domain_tools"

    account_id = "test_learner_02"
    quiz_tool = quiz_tool_cls()
    grade_tool = grade_tool_cls()

    quiz_out = quiz_tool.execute(
        GetQuizItemInput(lesson_id="money-basics-101"),
        account_id=account_id,
    )

    # Wrong answer -> rejected
    wrong_grade = grade_tool.execute(
        GradeCheckpointInput(checkpoint_id=quiz_out.checkpoint_id, response="Wrong cheating attempt"),
        account_id=account_id,
    )
    assert not wrong_grade.passed, "Grade must fail on wrong answer"
    assert wrong_grade.score == 0

    # Correct answer -> passed, verified event issued
    catalog = SqliteLearningCatalog()
    lesson = catalog.get_lesson(lesson_id="money-basics-101")
    matching_q = next((q for q in lesson.quiz_questions if q.prompt == quiz_out.prompt), lesson.quiz_questions[0])
    correct_option = matching_q.correct_answer

    passed_grade = grade_tool.execute(
        GradeCheckpointInput(checkpoint_id=quiz_out.checkpoint_id, response=correct_option),
        account_id=account_id,
    )
    assert passed_grade.passed, "Grade must pass on correct answer"
    assert passed_grade.score == 100
    assert passed_grade.verified_event_id.startswith("ev_")


def test_update_progress_idempotent():
    """GAP-6: Tool update_progress không được tích hợp vào agentic_core; gọi 2 lần chỉ ghi 1 lần."""
    manifest_update = get_default_tool_registry().get("learning.update_progress")
    assert manifest_update is not None, "Tool 'learning.update_progress' is missing from ToolRegistry"

    quiz_tool_cls = getattr(domain_tools, "LearningGetQuizItemTool", None)
    grade_tool_cls = getattr(domain_tools, "LearningGradeCheckpointTool", None)
    update_tool_cls = getattr(domain_tools, "LearningUpdateProgressTool", None)
    assert quiz_tool_cls is not None, "LearningGetQuizItemTool must be in domain_tools"
    assert grade_tool_cls is not None, "LearningGradeCheckpointTool must be in domain_tools"
    assert update_tool_cls is not None, "LearningUpdateProgressTool must be in domain_tools"

    account_id = "test_learner_03"
    quiz_tool = quiz_tool_cls()
    grade_tool = grade_tool_cls()
    update_tool = update_tool_cls()

    quiz_out = quiz_tool.execute(GetQuizItemInput(lesson_id="money-basics-101"), account_id=account_id)
    catalog = SqliteLearningCatalog()
    lesson = catalog.get_lesson(lesson_id="money-basics-101")
    matching_q = next((q for q in lesson.quiz_questions if q.prompt == quiz_out.prompt), lesson.quiz_questions[0])
    passed_grade = grade_tool.execute(
        GradeCheckpointInput(checkpoint_id=quiz_out.checkpoint_id, response=matching_q.correct_answer),
        account_id=account_id,
    )

    # First update call
    update_1 = update_tool.execute(
        UpdateProgressInput(
            verified_event_id=passed_grade.verified_event_id,
            idempotency_key="idemp_key_repeat",
            confirmation_id="conf_001",
        ),
        account_id=account_id,
    )
    assert update_1.status == "completed"

    # Second update call with same idempotency_key -> idempotent return
    update_2 = update_tool.execute(
        UpdateProgressInput(
            verified_event_id=passed_grade.verified_event_id,
            idempotency_key="idemp_key_repeat",
            confirmation_id="conf_001",
        ),
        account_id=account_id,
    )
    assert update_2.status == update_1.status
    assert update_2.quiz_score == update_1.quiz_score

    # Verify database persistence idempotency
    repo = SqliteLearningHomeRepository()
    records = repo.list_by_path(user_id=account_id, path_id="starter-foundations")
    completed_records = [r for r in records if r.lesson_id == "money-basics-101"]
    assert len(completed_records) == 1
