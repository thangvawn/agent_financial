from __future__ import annotations

from datetime import datetime, timedelta, timezone
import pytest

from risk_dashboard.modules.learning.application.checkpoint_service import LearningCheckpointService
from risk_dashboard.modules.learning.domain.entities import CheckpointRecord
from risk_dashboard.modules.learning.infrastructure.catalog_reader import SqliteLearningCatalog
from risk_dashboard.modules.learning.infrastructure.repositories.sqlite import (
    SqliteLearningCheckpointRepository,
    reset_learning_state,
)
from risk_dashboard.platform.database import open_app_state_db
from risk_dashboard.platform.database.migrate import apply_migrations


@pytest.fixture(autouse=True)
def setup_db():
    reset_learning_state()
    with open_app_state_db() as conn:
        apply_migrations(conn)


def test_checkpoint_expiry_rejection() -> None:
    service = LearningCheckpointService()
    account_id = "acct_expiring_01"

    # Create checkpoint with 0 ttl (already expired)
    cp_out = service.create_checkpoint(
        account_id=account_id,
        lesson_id="money-basics-101",
        ttl_seconds=-10,
    )

    with pytest.raises(ValueError, match="has expired"):
        service.grade_checkpoint(
            account_id=account_id,
            checkpoint_id=cp_out.checkpoint_id,
            response="some answer",
        )


def test_checkpoint_wrong_account_rejection() -> None:
    service = LearningCheckpointService()
    cp_out = service.create_checkpoint(
        account_id="valid_owner",
        lesson_id="money-basics-101",
    )

    with pytest.raises(PermissionError, match="does not belong to the authenticated account"):
        service.grade_checkpoint(
            account_id="attacker_account",
            checkpoint_id=cp_out.checkpoint_id,
            response="some answer",
        )


def test_verified_event_wrong_account_rejection_on_progress_update() -> None:
    service = LearningCheckpointService()
    cp_out = service.create_checkpoint(
        account_id="valid_owner",
        lesson_id="money-basics-101",
    )

    catalog = SqliteLearningCatalog()
    lesson = catalog.get_lesson(lesson_id="money-basics-101")
    matching_q = next((q for q in lesson.quiz_questions if q.prompt == cp_out.prompt), lesson.quiz_questions[0])

    grade_out = service.grade_checkpoint(
        account_id="valid_owner",
        checkpoint_id=cp_out.checkpoint_id,
        response=matching_q.correct_answer,
    )
    assert grade_out.passed

    with pytest.raises(PermissionError, match="does not belong to the authenticated account"):
        service.update_progress_confirmed(
            account_id="attacker_account",
            verified_event_id=grade_out.verified_event_id,
            idempotency_key="idemp_attack",
            confirmation_id="conf_attack",
        )


def test_zero_leakage_in_checkpoint_service() -> None:
    service = LearningCheckpointService()
    cp_out = service.create_checkpoint(
        account_id="learner_safe",
        lesson_id="money-basics-101",
    )

    out_dict = cp_out.model_dump()
    assert "correct_answer" not in out_dict
    assert "explanation" not in out_dict
    assert "answer_key" not in out_dict


def test_idempotent_duplicate_progress_updates() -> None:
    service = LearningCheckpointService()
    account_id = "learner_idemp"
    cp_out = service.create_checkpoint(
        account_id=account_id,
        lesson_id="money-basics-101",
    )
    catalog = SqliteLearningCatalog()
    lesson = catalog.get_lesson(lesson_id="money-basics-101")
    matching_q = next((q for q in lesson.quiz_questions if q.prompt == cp_out.prompt), lesson.quiz_questions[0])

    grade_out = service.grade_checkpoint(
        account_id=account_id,
        checkpoint_id=cp_out.checkpoint_id,
        response=matching_q.correct_answer,
    )

    # First update
    res1 = service.update_progress_confirmed(
        account_id=account_id,
        verified_event_id=grade_out.verified_event_id,
        idempotency_key="unique_key_123",
        confirmation_id="conf_123",
    )

    # Second update with same idempotency key
    res2 = service.update_progress_confirmed(
        account_id=account_id,
        verified_event_id=grade_out.verified_event_id,
        idempotency_key="unique_key_123",
        confirmation_id="conf_123",
    )

    assert res1.receipt_id == res2.receipt_id
    assert res1.status == res2.status == "completed"
    assert res1.updated_at == res2.updated_at


def test_grading_normalization_and_shortcuts() -> None:
    service = LearningCheckpointService()
    account_id = "test_norm_user"
    cp_out = service.create_checkpoint(
        account_id=account_id,
        lesson_id="money-basics-101",
    )

    catalog = SqliteLearningCatalog()
    lesson = catalog.get_lesson(lesson_id="money-basics-101")
    matching_q = next((q for q in lesson.quiz_questions if q.prompt == cp_out.prompt), lesson.quiz_questions[0])
    correct = matching_q.correct_answer

    # 1. Trailing whitespace and non-breaking space
    grade_ws = service.grade_checkpoint(
        account_id=account_id,
        checkpoint_id=cp_out.checkpoint_id,
        response=f"  {correct} \xa0 \u200b  ",
    )
    assert grade_ws.passed is True
    assert grade_ws.score == 100

    # 2. Option shortcut matching (e.g. index of correct answer in cp_out.options)
    correct_idx = cp_out.options.index(correct)
    shortcut_letters = ["A", "B", "C", "D", "E"]
    correct_letter = shortcut_letters[correct_idx]

    grade_shortcut_letter = service.grade_checkpoint(
        account_id=account_id,
        checkpoint_id=cp_out.checkpoint_id,
        response=f"Đáp án {correct_letter}",
    )
    assert grade_shortcut_letter.passed is True

    grade_shortcut_num = service.grade_checkpoint(
        account_id=account_id,
        checkpoint_id=cp_out.checkpoint_id,
        response=f"Option {correct_idx + 1}",
    )
    assert grade_shortcut_num.passed is True

    # 3. Wrong shortcut should fail
    wrong_idx = (correct_idx + 1) % len(cp_out.options)
    wrong_letter = shortcut_letters[wrong_idx]
    grade_wrong_shortcut = service.grade_checkpoint(
        account_id=account_id,
        checkpoint_id=cp_out.checkpoint_id,
        response=wrong_letter,
    )
    assert grade_wrong_shortcut.passed is False
    assert grade_wrong_shortcut.score == 0

