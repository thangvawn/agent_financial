from __future__ import annotations

from risk_dashboard.modules.learning.domain.entities import (
    LearningCoachNudge,
    LearningHomeState,
    LearningLesson,
    LearningPath,
    LearningProgress,
    LearningTutorReply,
    utc_now_iso,
)


def build_initial_learning_home_state(*, user_id: str, path: LearningPath, first_lesson: LearningLesson) -> LearningHomeState:
    return LearningHomeState(
        user_id=user_id,
        path_id=path.path_id,
        path_label=path.title,
        next_lesson_id=first_lesson.lesson_id,
        next_lesson_title=first_lesson.title,
        recommendation_summary=path.description,
        completed_lessons=0,
        completion_pct=0,
        updated_at=utc_now_iso(),
    )


def refresh_learning_home_state(
    *,
    user_id: str,
    path: LearningPath,
    lessons: list[LearningLesson],
    progress_items: list[LearningProgress],
) -> LearningHomeState:
    completed_ids = {item.lesson_id for item in progress_items if item.status == "completed"}
    next_lesson = next((lesson for lesson in lessons if lesson.lesson_id not in completed_ids), lessons[-1])
    completed_count = len(completed_ids)
    completion_pct = round((completed_count / max(len(lessons), 1)) * 100)
    summary = (
        f"Tiep tuc bai {next_lesson.title} de mo khoa buoc hanh dong tiep theo trong app."
        if completed_count < len(lessons)
        else "Ban da hoan thanh path nay. Hay ap dung vao Health, Goals hoac Guided Investing."
    )
    return LearningHomeState(
        user_id=user_id,
        path_id=path.path_id,
        path_label=path.title,
        next_lesson_id=next_lesson.lesson_id,
        next_lesson_title=next_lesson.title,
        recommendation_summary=summary,
        completed_lessons=completed_count,
        completion_pct=completion_pct,
        updated_at=utc_now_iso(),
    )


def complete_lesson_progress(
    *,
    user_id: str,
    path_id: str,
    lesson_id: str,
    previous: LearningProgress | None,
    quiz_score: int | None = None,
) -> LearningProgress:
    attempt_count = (previous.attempt_count if previous is not None else 0) + 1
    return LearningProgress(
        user_id=user_id,
        path_id=path_id,
        lesson_id=lesson_id,
        status="completed",
        quiz_score=quiz_score if quiz_score is not None else previous.quiz_score if previous else None,
        attempt_count=attempt_count,
        completed_at=utc_now_iso(),
        updated_at=utc_now_iso(),
    )


def quiz_progress(
    *,
    user_id: str,
    path_id: str,
    lesson_id: str,
    score: int,
    previous: LearningProgress | None,
) -> LearningProgress:
    return LearningProgress(
        user_id=user_id,
        path_id=path_id,
        lesson_id=lesson_id,
        status="completed" if score >= 60 else "in_progress",
        quiz_score=score,
        attempt_count=(previous.attempt_count if previous is not None else 0) + 1,
        completed_at=utc_now_iso() if score >= 60 else previous.completed_at if previous else None,
        updated_at=utc_now_iso(),
    )


def build_tutor_reply(*, lesson: LearningLesson, question: str, knowledge_level: str) -> LearningTutorReply:
    level_prefix = {
        "beginner": "Giai thich that don gian:",
        "basic": "Tom tat ngan gon:",
        "intermediate": "Giai thich co them mot chut context:",
        "advanced": "Ban tom tat nang cao:",
    }.get(knowledge_level, "Tom tat ngan gon:")
    first_block = lesson.body[0] if lesson.body else lesson.summary
    return LearningTutorReply(
        summary=f"{level_prefix} {lesson.summary}",
        explanation=f"{first_block} Cau hoi cua ban: {question}",
        check_question=lesson.quiz_questions[0].prompt if lesson.quiz_questions else "Neu phai dien dat lai bai nay bang 1 cau, ban se noi gi?",
        next_lesson_hint=lesson.next_lesson_id or "Ban co the quay lai Learn Home de xem bai tiep theo.",
    )


def build_coach_nudge(*, home_state: LearningHomeState, trigger: str) -> LearningCoachNudge:
    if trigger == "risk_score_low":
        return LearningCoachNudge(
            nudge_type="risk_score_low",
            title="Hoc risk basics truoc",
            message="Risk score thap la dau hieu nen quay lai bai co ban ve rui ro truoc khi mo rong tool.",
            cta_label=home_state.next_lesson_title,
            cta_path="/learn",
        )
    if trigger == "goal_off_track":
        return LearningCoachNudge(
            nudge_type="goal_off_track",
            title="Hoc trade-off cho goal",
            message="Goal dang cham tien do. Mot bai hoc ngan ve trade-off se giup ban dieu chinh deadline va pace thuc te hon.",
            cta_label=home_state.next_lesson_title,
            cta_path="/learn",
        )
    return LearningCoachNudge(
        nudge_type="continue_path",
        title="Tiep tuc path hien tai",
        message=home_state.recommendation_summary,
        cta_label=home_state.next_lesson_title,
        cta_path="/learn",
    )
