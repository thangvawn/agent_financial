from __future__ import annotations

from dataclasses import replace

from risk_dashboard.modules.analytics_monitoring.application.emitter import emit_product_event
from risk_dashboard.modules.community.application.services import GetCommunityHome
from risk_dashboard.modules.community.infrastructure.repositories.sqlite import (
    SqliteCommunityChallengeProgressRepository,
    SqliteCommunityMembershipRepository,
    SqliteCommunityNotificationRepository,
    SqliteCommunityPostRepository,
)
from risk_dashboard.modules.admin_cms.infrastructure.repositories.sqlite import SqliteAdminCmsRepository
from risk_dashboard.modules.financial_health.domain.entities import FinancialHealthSnapshot
from risk_dashboard.modules.financial_health.domain.ports import FinancialHealthSnapshotRepository
from risk_dashboard.modules.goals.domain.entities import Goal, GoalSnapshot
from risk_dashboard.modules.goals.domain.ports import GoalHomeReader
from risk_dashboard.modules.home_onboarding.domain.entities import OnboardingProfile, OnboardingSession, utc_now_iso
from risk_dashboard.modules.home_onboarding.domain.policies import build_home_state, decide_route
from risk_dashboard.modules.home_onboarding.domain.ports import (
    HomeStateRepository,
    OnboardingProfileRepository,
    OnboardingSessionRepository,
)
from risk_dashboard.modules.learning.application.services import SeedLearningHome
from risk_dashboard.modules.learning.domain.entities import LearningHomeState
from risk_dashboard.modules.learning.domain.ports import LearningHomeReader, LearningHomeWriter
from risk_dashboard.modules.learning.infrastructure.catalog_reader import SqliteLearningCatalog
from risk_dashboard.modules.home_onboarding.schemas.requests import OnboardingAnswerItem
from risk_dashboard.modules.home_onboarding.schemas.responses import (
    HomeResponse,
    HomeBlockResponse,
    HomeGoalSnapshotResponse,
    HomeHealthSnapshotResponse,
    HomeCommunitySnapshotResponse,
    OnboardingCompleteResponse,
    OnboardingSessionResponse,
)
from risk_dashboard.platform.security.access_control import assign_role


class StartOnboarding:
    def __init__(self, sessions: OnboardingSessionRepository) -> None:
        self.sessions = sessions

    def execute(self) -> OnboardingSessionResponse:
        session = self.sessions.create()
        emit_product_event(
            event_name="onboarding_started",
            module="home_onboarding",
            surface="onboarding",
            session_id=session.session_id,
            properties={"questions": 5},
        )
        return OnboardingSessionResponse(
            session_id=session.session_id,
            current_step=session.last_step,
            questions=(
                "primary_goal",
                "knowledge_level",
                "primary_interest",
                "current_state",
                "risk_tolerance_prelim",
            ),
        )


class AnswerOnboardingQuestion:
    def __init__(self, sessions: OnboardingSessionRepository) -> None:
        self.sessions = sessions

    def execute(self, *, session_id: str, answers: list[OnboardingAnswerItem]) -> OnboardingSessionResponse:
        session = self.sessions.get(session_id)
        if session is None:
            raise ValueError("Unknown onboarding session.")

        updated_answers = dict(session.answers)
        for answer in answers:
            updated_answers[answer.question_key] = answer.answer_value

        last_step = answers[-1].question_key if answers else session.last_step
        updated_session = replace(session, answers=updated_answers, last_step=last_step)
        saved = self.sessions.save(updated_session)
        return OnboardingSessionResponse(
            session_id=saved.session_id,
            current_step=saved.last_step,
            questions=(
                "primary_goal",
                "knowledge_level",
                "primary_interest",
                "current_state",
                "risk_tolerance_prelim",
            ),
        )


class CompleteOnboarding:
    def __init__(
        self,
        sessions: OnboardingSessionRepository,
        profiles: OnboardingProfileRepository,
        home_states: HomeStateRepository,
        learning_home_writer: LearningHomeWriter | None = None,
    ) -> None:
        self.sessions = sessions
        self.profiles = profiles
        self.home_states = home_states
        self.learning_home_writer = learning_home_writer

    def execute(self, *, session_id: str) -> OnboardingCompleteResponse:
        session = self.sessions.get(session_id)
        if session is None:
            raise ValueError("Unknown onboarding session.")

        required_keys = {
            "primary_goal",
            "knowledge_level",
            "primary_interest",
            "current_state",
            "risk_tolerance_prelim",
        }
        missing = sorted(required_keys - set(session.answers))
        if missing:
            raise ValueError(f"Missing onboarding answers: {', '.join(missing)}")

        decision = decide_route(
            primary_goal=session.answers["primary_goal"],
            knowledge_level=session.answers["knowledge_level"],
            risk_tolerance_prelim=session.answers["risk_tolerance_prelim"],
            primary_interest=session.answers["primary_interest"],
            current_state=session.answers["current_state"],
        )
        now = utc_now_iso()
        profile = OnboardingProfile(
            session_id=session_id,
            primary_goal=session.answers["primary_goal"],
            knowledge_level=session.answers["knowledge_level"],
            risk_tolerance_prelim=session.answers["risk_tolerance_prelim"],
            primary_interest=session.answers["primary_interest"],
            current_state=session.answers["current_state"],
            persona_segment=decision.persona_segment,
            guided_investing_eligible=decision.guided_investing_eligible,
            pro_eligible=decision.pro_eligible,
            primary_route=decision.primary_route,
            created_at=now,
            updated_at=now,
        )
        self.profiles.save(profile)
        self.sessions.save(replace(session, completed_at=now))
        assign_role(actor_id=session_id, role="public_user")
        if decision.pro_eligible:
            assign_role(actor_id=session_id, role="pro_lab_user")

        home_state = build_home_state(session_id=session_id, decision=decision)
        self.home_states.save(home_state)
        if self.learning_home_writer is not None:
            SeedLearningHome(
                self.learning_home_writer,
                catalog=_StaticLearningCatalog(),
            ).execute(
                user_id=session_id,
                persona_segment=decision.persona_segment,
                primary_route=decision.primary_route,
            )
        emit_product_event(
            event_name="onboarding_completed",
            module="home_onboarding",
            surface="onboarding",
            session_id=session_id,
            persona_segment=decision.persona_segment,
            route=decision.primary_route,
            properties={
                "persona": decision.persona_segment,
                "route": decision.primary_route,
                "guided_investing_eligible": decision.guided_investing_eligible,
                "pro_eligible": decision.pro_eligible,
            },
        )
        emit_product_event(
            event_name="persona_assigned",
            module="home_onboarding",
            surface="onboarding",
            session_id=session_id,
            persona_segment=decision.persona_segment,
            properties={"persona": decision.persona_segment},
        )
        emit_product_event(
            event_name="primary_route_assigned",
            module="home_onboarding",
            surface="home",
            session_id=session_id,
            persona_segment=decision.persona_segment,
            route=decision.primary_route,
            properties={"route": decision.primary_route},
        )

        return OnboardingCompleteResponse(
            session_id=session_id,
            persona_segment=decision.persona_segment,
            primary_route=decision.primary_route,
            guided_investing_eligible=decision.guided_investing_eligible,
            pro_eligible=decision.pro_eligible,
            trust_message=decision.trust_message,
            next_best_action_type=home_state.next_best_action_type,
            next_best_action_ref=home_state.next_best_action_ref,
        )


class GetHomeState:
    def __init__(
        self,
        profiles: OnboardingProfileRepository,
        home_states: HomeStateRepository,
        financial_health_snapshots: FinancialHealthSnapshotRepository | None = None,
        learning_home_reader: LearningHomeReader | None = None,
        goal_home_reader: GoalHomeReader | None = None,
    ) -> None:
        self.profiles = profiles
        self.home_states = home_states
        self.financial_health_snapshots = financial_health_snapshots
        self.learning_home_reader = learning_home_reader
        self.goal_home_reader = goal_home_reader

    def execute(self, *, session_id: str) -> HomeResponse:
        profile = self.profiles.get(session_id)
        state = self.home_states.get(session_id)
        if profile is None or state is None:
            raise ValueError("Home is unavailable before onboarding is completed.")

        financial_health_snapshot = None
        if self.financial_health_snapshots is not None:
            financial_health_snapshot = self.financial_health_snapshots.get(session_id)

        learning_home_state = None
        if self.learning_home_reader is not None:
            try:
                learning_home_state = self.learning_home_reader.get_home_state(user_id=session_id)
            except ValueError:
                learning_home_state = None

        latest_goal_summary = None
        if self.goal_home_reader is not None:
            latest_goal_summary = self.goal_home_reader.get_latest_goal_summary(session_id)

        effective_guided_investing_eligible = profile.guided_investing_eligible
        next_best_action_type = state.next_best_action_type
        next_best_action_ref = state.next_best_action_ref
        if financial_health_snapshot is not None:
            effective_guided_investing_eligible = financial_health_snapshot.guided_investing_eligible
            if (
                state.next_best_action_type == "setup_financial_health"
                or (
                    profile.primary_route in {"guided_investing", "insights"}
                    and not financial_health_snapshot.guided_investing_eligible
                    and financial_health_snapshot.actions
                )
            ):
                next_best_action_type = financial_health_snapshot.actions[0].code
                next_best_action_ref = financial_health_snapshot.actions[0].cta_path or state.next_best_action_ref
        if latest_goal_summary is not None:
            latest_goal, latest_goal_snapshot = latest_goal_summary
            if latest_goal_snapshot.feasibility_band in {"high_stress", "not_feasible_yet"}:
                next_best_action_type = "stabilize_goal_plan"
                next_best_action_ref = "/goals"
            elif latest_goal_snapshot.feasibility_band in {"on_track", "stretch"}:
                next_best_action_type = "review_goal_progress"
                next_best_action_ref = latest_goal.goal_id
        elif profile.primary_route == "learn" and learning_home_state is not None:
            next_best_action_type = "continue_learning_path"
            next_best_action_ref = learning_home_state.next_lesson_id

        blocks = _build_blocks(state, financial_health_snapshot, learning_home_state, latest_goal_summary)
        trust_message = state.trust_message
        content_ops_nudge = _resolve_home_nudge(
            trigger_type=next_best_action_type,
            persona_segment=profile.persona_segment,
        )
        if content_ops_nudge is not None:
            trust_message = str(content_ops_nudge.get("message_template") or trust_message)
            blocks = _apply_home_nudge_to_blocks(
                blocks=blocks,
                title=str(content_ops_nudge.get("title_template") or "What should I do next?"),
                message=str(content_ops_nudge.get("message_template") or ""),
                cta_label=str(content_ops_nudge.get("cta_label") or ""),
                cta_path=str(content_ops_nudge.get("cta_path_template") or ""),
            )

        emit_product_event(
            event_name="home_loaded_after_onboarding",
            module="home_onboarding",
            surface="home",
            session_id=session_id,
            persona_segment=profile.persona_segment,
            route=profile.primary_route,
            properties={
                "guided_investing_eligible": effective_guided_investing_eligible,
                "next_best_action_type": next_best_action_type,
            },
        )
        return HomeResponse(
            session_id=session_id,
            persona_segment=profile.persona_segment,
            primary_route=profile.primary_route,
            guided_investing_eligible=effective_guided_investing_eligible,
            pro_eligible=profile.pro_eligible,
            next_best_action_type=next_best_action_type,
            next_best_action_ref=next_best_action_ref,
            trust_message=trust_message,
            blocks=blocks,
            health_snapshot=_build_health_snapshot_summary(financial_health_snapshot),
            goal_snapshot=_build_goal_snapshot_summary(latest_goal_summary),
            community_snapshot=_build_community_snapshot_summary(session_id),
        )


def _build_blocks(
    state,
    financial_health_snapshot: FinancialHealthSnapshot | None,
    learning_home_state: LearningHomeState | None,
    latest_goal_summary: tuple[Goal, GoalSnapshot] | None,
) -> list[dict[str, str | None]]:
    blocks: list[dict[str, str | None]] = []
    for block in state.blocks:
        if block.block_id == "health_snapshot" and financial_health_snapshot is not None:
            next_action = financial_health_snapshot.actions[0] if financial_health_snapshot.actions else None
            top_flag = financial_health_snapshot.flags[0].title if financial_health_snapshot.flags else "Chưa có cảnh báo lớn"
            blocks.append(
                {
                    "block_id": block.block_id,
                    "title": block.title,
                    "description": (
                        f"Điểm hiện tại {financial_health_snapshot.health_score}/100 ({financial_health_snapshot.score_band}). "
                        f"Ưu tiên lúc này: {top_flag}."
                    ),
                    "cta_label": next_action.title if next_action is not None else "Xem Financial Health",
                    "cta_path": next_action.cta_path if next_action is not None else "/financial-health",
                }
            )
            continue

        if block.block_id == "goals_snapshot" and latest_goal_summary is not None:
            goal, goal_snapshot = latest_goal_summary
            next_action = goal_snapshot.actions[0] if goal_snapshot.actions else None
            blocks.append(
                {
                    "block_id": block.block_id,
                    "title": block.title,
                    "description": (
                        f"{goal.goal_name}: con thieu {goal_snapshot.gap_amount:,.0f} {goal.currency} "
                        f"trong {goal_snapshot.months_remaining} thang."
                    ),
                    "cta_label": next_action.title if next_action is not None else "Xem ke hoach muc tieu",
                    "cta_path": next_action.cta_path if next_action is not None else "/goals",
                }
            )
            continue

        if block.block_id == "learning_recommendation" and learning_home_state is not None:
            lesson_title = learning_home_state.next_lesson_title
            description = learning_home_state.recommendation_summary
            if financial_health_snapshot is not None:
                learning_link = next(
                    (item for item in financial_health_snapshot.educational_links if item.get("kind") == "lesson"),
                    None,
                )
                if learning_link is not None:
                    lesson_title = learning_link["title"]
            blocks.append(
                {
                    "block_id": block.block_id,
                    "title": block.title,
                    "description": description,
                    "cta_label": lesson_title,
                    "cta_path": "/learn",
                }
            )
            continue

        if block.block_id == "insight_recommendation" and financial_health_snapshot is not None:
            description = block.description
            if not financial_health_snapshot.guided_investing_eligible:
                description = "Guided Investing sẽ mở khi nền tảng tài chính của bạn ổn định hơn."
            blocks.append(
                {
                    "block_id": block.block_id,
                    "title": block.title,
                    "description": description,
                    "cta_label": block.cta_label,
                    "cta_path": block.cta_path,
                }
            )
            continue

        blocks.append(
            {
                "block_id": block.block_id,
                "title": block.title,
                "description": block.description,
                "cta_label": block.cta_label,
                "cta_path": block.cta_path,
            }
        )
    return blocks


def _build_health_snapshot_summary(
    financial_health_snapshot: FinancialHealthSnapshot | None,
) -> HomeHealthSnapshotResponse | None:
    if financial_health_snapshot is None:
        return None

    next_action = financial_health_snapshot.actions[0] if financial_health_snapshot.actions else None
    return HomeHealthSnapshotResponse(
        health_score=financial_health_snapshot.health_score,
        score_band=financial_health_snapshot.score_band,
        guided_investing_eligible=financial_health_snapshot.guided_investing_eligible,
        summary=(
            f"Điểm Financial Health của bạn là {financial_health_snapshot.health_score}/100. "
            f"Trạng thái hiện tại: {financial_health_snapshot.score_band}."
        ),
        top_flags=[item.title for item in financial_health_snapshot.flags[:3]],
        next_action_title=next_action.title if next_action is not None else None,
        next_action_path=next_action.cta_path if next_action is not None else None,
    )


def _build_goal_snapshot_summary(
    latest_goal_summary: tuple[Goal, GoalSnapshot] | None,
) -> HomeGoalSnapshotResponse | None:
    if latest_goal_summary is None:
        return None
    goal, goal_snapshot = latest_goal_summary
    next_action = goal_snapshot.actions[0] if goal_snapshot.actions else None
    return HomeGoalSnapshotResponse(
        goal_id=goal.goal_id,
        goal_name=goal.goal_name,
        goal_type=goal.goal_type,
        current_amount=goal.current_amount,
        target_amount=goal.target_amount,
        currency=goal.currency,
        gap_amount=goal_snapshot.gap_amount,
        monthly_contribution_needed=goal_snapshot.monthly_contribution_needed,
        feasibility_band=goal_snapshot.feasibility_band,
        months_remaining=goal_snapshot.months_remaining,
        reminder_status=_goal_reminder_status(goal_snapshot),
        next_reminder_at=None,
        summary=(
            f"Muc tieu {goal.goal_name} dang o muc {goal_snapshot.feasibility_band}. "
            f"Ban can xap xi {goal_snapshot.monthly_contribution_needed:,.0f} {goal.currency}/thang."
        ),
        next_action_title=next_action.title if next_action is not None else "Xem ke hoach muc tieu",
        next_action_path=next_action.cta_path if next_action is not None else "/goals",
    )


def _goal_reminder_status(goal_snapshot: GoalSnapshot) -> str:
    if goal_snapshot.feasibility_band in {"high_stress", "not_feasible_yet"}:
        return "off_track"
    if goal_snapshot.months_remaining <= 3:
        return "due_soon"
    return "on_track"


def _build_community_snapshot_summary(session_id: str) -> HomeCommunitySnapshotResponse | None:
    community_home = GetCommunityHome(
        memberships=SqliteCommunityMembershipRepository(),
        posts=SqliteCommunityPostRepository(),
        challenges=SqliteCommunityChallengeProgressRepository(),
        notifications=SqliteCommunityNotificationRepository(),
    ).execute(user_id=session_id)

    recommended_space_id = community_home.recommended_space_ids[0] if community_home.recommended_space_ids else None
    recommended_space = next(
        (space for space in community_home.spaces if space.space_id == recommended_space_id),
        None,
    )
    challenge = community_home.challenge_progress[0] if community_home.challenge_progress else None
    notification = community_home.notifications[0] if community_home.notifications else None
    if recommended_space is None and challenge is None and not community_home.memberships:
        return None

    if notification is not None:
        summary = notification.message
    elif challenge is not None:
        summary = (
            f"Challenge {challenge.challenge_id} hiện ở mức {challenge.progress_pct}% "
            f"({challenge.status}). Đây là vòng quay tốt để quay lại app đều hơn."
        )
    elif recommended_space is not None:
        summary = (
            f"Space được gợi ý tiếp theo là {recommended_space.title}. "
            "Community ở đây để học cùng có kiểm soát, không phải room tín hiệu."
        )
    else:
        summary = "Bạn đã có mặt trong Community. Hãy quay lại space đang theo dõi để giữ nhịp học và check-in."

    action_path = (
        f"/community?space={challenge.challenge_id}"
        if challenge is not None
        else (f"/community?space={recommended_space.space_id}" if recommended_space is not None else "/community")
    )
    return HomeCommunitySnapshotResponse(
        recommended_space_id=recommended_space.space_id if recommended_space is not None else None,
        recommended_space_title=recommended_space.title if recommended_space is not None else None,
        joined_space_count=len(community_home.memberships),
        challenge_id=challenge.challenge_id if challenge is not None else None,
        challenge_status=challenge.status if challenge is not None else None,
        challenge_progress_pct=challenge.progress_pct if challenge is not None else None,
        active_notification_count=len(community_home.notifications),
        next_notification_title=notification.title if notification is not None else None,
        next_notification_path=notification.cta_path if notification is not None else None,
        summary=summary,
        next_action_title=(
            notification.title
            if notification is not None
            else (
                "Mở Community challenge"
                if challenge is not None
                else ("Tham gia Community" if recommended_space is not None else "Mở Community")
            )
        ),
        next_action_path=(
            notification.cta_path
            if notification is not None
            else action_path
        ),
    )


def _resolve_home_nudge(*, trigger_type: str, persona_segment: str) -> dict[str, object] | None:
    repo = SqliteAdminCmsRepository()
    for item, version in repo.list_published_content(content_type="nudge_template"):
        payload = version.payload
        surface = str(payload.get("surface") or "home")
        if surface != "home":
            continue
        payload_trigger = str(payload.get("trigger_type") or "").strip()
        if payload_trigger and payload_trigger != trigger_type:
            continue
        persona_tags = payload.get("persona_tags") or []
        if isinstance(persona_tags, list) and persona_tags and persona_segment not in {str(tag) for tag in persona_tags}:
            continue
        return payload
    return None


def _apply_home_nudge_to_blocks(
    *,
    blocks: list[dict[str, str | None]],
    title: str,
    message: str,
    cta_label: str,
    cta_path: str,
) -> list[dict[str, str | None]]:
    updated_blocks: list[dict[str, str | None]] = []
    for block in blocks:
        if block["block_id"] != "next_best_action":
            updated_blocks.append(block)
            continue
        updated_blocks.append(
            HomeBlockResponse(
                block_id=block["block_id"],
                title=title or block["title"],
                description=message or block["description"],
                cta_label=cta_label or block.get("cta_label"),
                cta_path=cta_path or block.get("cta_path"),
            ).model_dump()
        )
    return updated_blocks


class _StaticLearningCatalog:
    def __init__(self) -> None:
        self.catalog = SqliteLearningCatalog()

    def get_path_for_persona(self, *, persona_segment: str, primary_route: str):
        return self.catalog.get_path_for_persona(persona_segment=persona_segment, primary_route=primary_route)

    def get_lesson(self, *, lesson_id: str):
        return self.catalog.get_lesson(lesson_id=lesson_id)
