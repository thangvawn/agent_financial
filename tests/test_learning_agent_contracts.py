from __future__ import annotations

import pytest
from pydantic import ValidationError

from risk_dashboard.modules.learning.schemas.agent_tools import (
    GetContextInput,
    GetContextOutput,
    GetProgressInput,
    GetProgressOutput,
    GetQuizItemInput,
    GetQuizItemOutput,
    GradeCheckpointInput,
    GradeCheckpointOutput,
    ProgressItem,
    RecommendedItem,
    RecommendNextInput,
    RecommendNextOutput,
    SourceRef,
    UpdateProgressInput,
    UpdateProgressOutput,
)


def test_schema_version_freeze_at_1_0_0() -> None:
    schemas = [
        GetContextInput(lesson_id="l1"),
        GetContextOutput(
            lesson_id="l1",
            title="Title",
            canonical_content=("Content 1",),
            sources=(SourceRef(source_id="s1", content_version="v1"),),
            publication_status="published",
        ),
        GetProgressInput(path_id="p1"),
        GetProgressOutput(
            path_id="p1",
            items=(
                ProgressItem(
                    lesson_id="l1",
                    status="completed",
                    attempt_count=1,
                    updated_at="2026-09-02T10:00:00Z",
                ),
            ),
            completion_pct=100,
        ),
        GetQuizItemInput(lesson_id="l1"),
        GetQuizItemOutput(
            checkpoint_id="cp_123",
            lesson_id="l1",
            prompt="What is ROE?",
            options=("A", "B", "C"),
            expires_at="2026-09-02T10:15:00Z",
        ),
        GradeCheckpointInput(checkpoint_id="cp_123", response="A"),
        GradeCheckpointOutput(
            checkpoint_id="cp_123",
            lesson_id="l1",
            passed=True,
            score=100,
            rubric_evidence=("Correct calculation",),
            verified_event_id="ev_123",
        ),
        UpdateProgressInput(
            verified_event_id="ev_123",
            idempotency_key="idemp_123",
            confirmation_id="conf_123",
        ),
        UpdateProgressOutput(
            receipt_id="rcpt_123",
            lesson_id="l1",
            status="completed",
            updated_at="2026-09-02T10:00:00Z",
        ),
        RecommendNextInput(path_id="p1"),
        RecommendNextOutput(
            path_id="p1",
            items=(
                RecommendedItem(
                    lesson_id="l2",
                    title="Next Lesson",
                    rank=1,
                    rationale="Next in sequence",
                ),
            ),
        ),
    ]

    for s in schemas:
        assert s.schema_version == "1.0.0"


def test_zero_leakage_in_checkpoint_and_quiz_schemas() -> None:
    quiz_out_fields = set(GetQuizItemOutput.model_fields.keys())
    grade_out_fields = set(GradeCheckpointOutput.model_fields.keys())

    forbidden_fields = {"correct_answer", "answer", "answer_key", "key", "grading_key"}
    assert not (quiz_out_fields & forbidden_fields), f"Found forbidden secret field in GetQuizItemOutput: {quiz_out_fields & forbidden_fields}"
    assert not (grade_out_fields & forbidden_fields), f"Found forbidden secret field in GradeCheckpointOutput: {grade_out_fields & forbidden_fields}"


def test_immutable_sequences_use_tuples() -> None:
    context_out = GetContextOutput(
        lesson_id="l1",
        title="Title",
        canonical_content=["Content 1", "Content 2"],  # type: ignore[arg-type]
        objectives=["Obj 1"],  # type: ignore[arg-type]
        sources=[SourceRef(source_id="s1", content_version="v1")],  # type: ignore[arg-type]
        publication_status="published",
    )
    assert isinstance(context_out.canonical_content, tuple)
    assert isinstance(context_out.objectives, tuple)
    assert isinstance(context_out.sources, tuple)


def test_client_input_validation_and_authority() -> None:
    # Inputs do not have account_id fields (account_id is strictly server-resolved)
    for inp_cls in [
        GetContextInput,
        GetProgressInput,
        GetQuizItemInput,
        GradeCheckpointInput,
        UpdateProgressInput,
        RecommendNextInput,
    ]:
        assert "account_id" not in inp_cls.model_fields
        assert "user_id" not in inp_cls.model_fields


def test_round_trip_serialization() -> None:
    orig = GetContextOutput(
        lesson_id="l1",
        title="Title",
        canonical_content=("Content 1", "Content 2"),
        objectives=("Obj 1",),
        sources=(SourceRef(source_id="s1", content_version="1.0.0", section_id="sec_1"),),
        publication_status="published",
    )
    json_data = orig.model_dump_json()
    reconstructed = GetContextOutput.model_validate_json(json_data)
    assert reconstructed == orig

