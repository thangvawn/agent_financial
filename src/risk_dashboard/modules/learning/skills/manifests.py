from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class SkillManifest:
    skill_id: str
    version: str
    name: str
    description: str
    target_surface: str
    required_tools: tuple[str, ...]
    max_steps: int = 4
    zero_leakage_enforced: bool = False


EXPLAIN_SKILL_V1 = SkillManifest(
    skill_id="learn.explain.v1",
    version="1.0.0",
    name="Lesson Explainer",
    description="Explain lesson concepts and sections tailored to user knowledge level (beginner/intermediate/advanced).",
    target_surface="learn",
    required_tools=("learning.get_context",),
)

SOCRATIC_HINT_SKILL_V1 = SkillManifest(
    skill_id="learn.socratic_hint.v1",
    version="1.0.0",
    name="Socratic Quiz Hint",
    description="Provide pedagogical multi-stage hints without leaking the correct answer key.",
    target_surface="learn",
    required_tools=("learning.get_quiz_item",),
    zero_leakage_enforced=True,
)

FORMULA_WALKTHROUGH_SKILL_V1 = SkillManifest(
    skill_id="learn.formula_walkthrough.v1",
    version="1.0.0",
    name="Formula Walkthrough",
    description="Break down quantitative formulas into variables, sample substitutions, units, and economic rationale.",
    target_surface="learn",
    required_tools=("learning.get_context",),
)

CHECK_MISCONCEPTION_SKILL_V1 = SkillManifest(
    skill_id="learn.check_misconception.v1",
    version="1.0.0",
    name="Misconception Detector",
    description="Identify and gently clarify financial misconceptions in learner responses.",
    target_surface="learn",
    required_tools=("learning.get_context",),
)

RUN_CHECKPOINT_SKILL_V1 = SkillManifest(
    skill_id="learn.run_checkpoint.v1",
    version="1.0.0",
    name="Run Learning Checkpoint",
    description="Coordinate checkpoint presentation, secure server-side grading, and verified event generation.",
    target_surface="learn",
    required_tools=("learning.get_quiz_item", "learning.grade_checkpoint", "learning.update_progress"),
)

NEXT_STEP_SKILL_V1 = SkillManifest(
    skill_id="learn.next_step.v1",
    version="1.0.0",
    name="Next Step Recommendation",
    description="Suggest next personalized lesson cards based on curriculum path and completed progress.",
    target_surface="learn",
    required_tools=("learning.recommend_next", "learning.get_progress"),
)


ALL_LEARNING_SKILLS: tuple[SkillManifest, ...] = (
    EXPLAIN_SKILL_V1,
    SOCRATIC_HINT_SKILL_V1,
    FORMULA_WALKTHROUGH_SKILL_V1,
    CHECK_MISCONCEPTION_SKILL_V1,
    RUN_CHECKPOINT_SKILL_V1,
    NEXT_STEP_SKILL_V1,
)


def get_skill_manifest(skill_id: str) -> SkillManifest | None:
    for s in ALL_LEARNING_SKILLS:
        if s.skill_id == skill_id:
            return s
    return None

