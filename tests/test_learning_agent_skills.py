from __future__ import annotations

import pytest

from risk_dashboard.modules.learning.skills.manifests import (
    ALL_LEARNING_SKILLS,
    CHECK_MISCONCEPTION_SKILL_V1,
    EXPLAIN_SKILL_V1,
    FORMULA_WALKTHROUGH_SKILL_V1,
    NEXT_STEP_SKILL_V1,
    RUN_CHECKPOINT_SKILL_V1,
    SOCRATIC_HINT_SKILL_V1,
    get_skill_manifest,
)
from risk_dashboard.modules.learning.skills.prompts import (
    EXPLAIN_SYSTEM_PROMPT,
    FORMULA_WALKTHROUGH_SYSTEM_PROMPT,
    MISCONCEPTION_SYSTEM_PROMPT,
    NEXT_STEP_SYSTEM_PROMPT,
    RUN_CHECKPOINT_SYSTEM_PROMPT,
    SOCRATIC_HINT_SYSTEM_PROMPT,
    build_explain_prompt,
    build_formula_prompt,
    build_misconception_prompt,
    build_next_step_prompt,
    build_run_checkpoint_prompt,
    build_socratic_hint_prompt,
)


def test_learning_skill_manifests() -> None:
    assert len(ALL_LEARNING_SKILLS) == 6
    skill_ids = {s.skill_id for s in ALL_LEARNING_SKILLS}
    expected_ids = {
        "learn.explain.v1",
        "learn.socratic_hint.v1",
        "learn.formula_walkthrough.v1",
        "learn.check_misconception.v1",
        "learn.run_checkpoint.v1",
        "learn.next_step.v1",
    }
    assert skill_ids == expected_ids

    for s in ALL_LEARNING_SKILLS:
        assert s.version == "1.0.0"
        assert s.target_surface == "learn"
        assert s.required_tools

    assert SOCRATIC_HINT_SKILL_V1.zero_leakage_enforced is True
    assert get_skill_manifest("learn.explain.v1") == EXPLAIN_SKILL_V1
    assert get_skill_manifest("non_existent") is None


def test_socratic_hint_prompt_zero_leakage() -> None:
    prompt = build_socratic_hint_prompt(
        prompt_text="Chỉ số ROE là gì?",
        options=("Lợi nhuận ròng / Vốn chủ sở hữu", "Doanh thu / Chi phí", "Nợ / Tài sản"),
        user_query="Cho em gợi ý làm câu này với ạ",
    )

    # Must contain options and question
    assert "Chỉ số ROE là gì?" in prompt
    assert "Lợi nhuận ròng / Vốn chủ sở hữu" in prompt
    assert "Cho em gợi ý làm câu này" in prompt

    # Must not contain answers or answer keys
    forbidden_tokens = ["correct_answer", "answer_key", "chọn đáp án", "đáp án đúng là"]
    for token in forbidden_tokens:
        assert token not in prompt.lower()

    # System prompt must enforce zero leakage
    assert "ZERO LEAKAGE" in SOCRATIC_HINT_SYSTEM_PROMPT
    assert "TUYỆT ĐỐI KHÔNG" in SOCRATIC_HINT_SYSTEM_PROMPT


def test_explain_prompt_structure() -> None:
    prompt = build_explain_prompt(
        lesson_title="Tien co ban",
        content="Tien khong chi la thu nhap...",
        user_query="Giai thich giup toi.",
        knowledge_level="beginner",
    )
    assert "Tien co ban" in prompt
    assert "beginner" in prompt
    assert "Tien khong chi la thu nhap" in prompt
    assert "Giai thich giup toi" in prompt


def test_formula_walkthrough_prompt_structure() -> None:
    prompt = build_formula_prompt(
        formula_name="ROE",
        raw_content="ROE = Net Income / Equity",
        user_query="Phan tich cong thuc nay.",
    )
    assert "ROE" in prompt
    assert "Net Income / Equity" in prompt
    assert "Phan tich cong thuc nay" in prompt


def test_misconception_prompt_structure() -> None:
    prompt = build_misconception_prompt(
        user_statement="Doanh thu cao thi chac chan loi nhuan tot va an toan.",
        lesson_context="Dong tien va loi nhuan co the khac biet do phai thu va chi phi von.",
    )
    assert "Doanh thu cao" in prompt
    assert "Dong tien va loi nhuan" in prompt


def test_next_step_prompt_structure() -> None:
    prompt = build_next_step_prompt(
        path_title="Nha dau tu co ban",
        completion_pct=50,
        recommendations=[{"title": "Dong tien", "rationale": "Buoc tiep theo"}],
    )
    assert "Nha dau tu co ban" in prompt
    assert "50%" in prompt
    assert "Dong tien" in prompt

