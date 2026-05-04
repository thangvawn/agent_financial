from __future__ import annotations

import json
import uuid

from risk_dashboard.modules.home_onboarding.domain.entities import HomeBlock, HomeState, OnboardingProfile, OnboardingSession
from risk_dashboard.modules.home_onboarding.domain.ports import (
    HomeStateRepository,
    OnboardingProfileRepository,
    OnboardingSessionRepository,
)
from risk_dashboard.platform.database import open_app_state_db, reset_app_state_tables


class SqliteOnboardingSessionRepository(OnboardingSessionRepository):
    def create(self) -> OnboardingSession:
        session = OnboardingSession(session_id=str(uuid.uuid4()))
        return self.save(session)

    def get(self, session_id: str) -> OnboardingSession | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT session_id, started_at, last_step, answers_json, completed_at
                FROM onboarding_sessions
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        return OnboardingSession(
            session_id=row["session_id"],
            started_at=row["started_at"],
            last_step=row["last_step"],
            answers=json.loads(row["answers_json"] or "{}"),
            completed_at=row["completed_at"],
        )

    def save(self, session: OnboardingSession) -> OnboardingSession:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO onboarding_sessions (session_id, started_at, last_step, answers_json, completed_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    started_at = excluded.started_at,
                    last_step = excluded.last_step,
                    answers_json = excluded.answers_json,
                    completed_at = excluded.completed_at
                """,
                (
                    session.session_id,
                    session.started_at,
                    session.last_step,
                    json.dumps(session.answers, ensure_ascii=False),
                    session.completed_at,
                ),
            )
            conn.commit()
        return session


class SqliteOnboardingProfileRepository(OnboardingProfileRepository):
    def save(self, profile: OnboardingProfile) -> OnboardingProfile:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO onboarding_profiles (
                    session_id, primary_goal, knowledge_level, risk_tolerance_prelim, primary_interest,
                    current_state, persona_segment, guided_investing_eligible, pro_eligible, primary_route,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    primary_goal = excluded.primary_goal,
                    knowledge_level = excluded.knowledge_level,
                    risk_tolerance_prelim = excluded.risk_tolerance_prelim,
                    primary_interest = excluded.primary_interest,
                    current_state = excluded.current_state,
                    persona_segment = excluded.persona_segment,
                    guided_investing_eligible = excluded.guided_investing_eligible,
                    pro_eligible = excluded.pro_eligible,
                    primary_route = excluded.primary_route,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at
                """,
                (
                    profile.session_id,
                    profile.primary_goal,
                    profile.knowledge_level,
                    profile.risk_tolerance_prelim,
                    profile.primary_interest,
                    profile.current_state,
                    profile.persona_segment,
                    int(profile.guided_investing_eligible),
                    int(profile.pro_eligible),
                    profile.primary_route,
                    profile.created_at,
                    profile.updated_at,
                ),
            )
            conn.commit()
        return profile

    def get(self, session_id: str) -> OnboardingProfile | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT session_id, primary_goal, knowledge_level, risk_tolerance_prelim, primary_interest,
                       current_state, persona_segment, guided_investing_eligible, pro_eligible, primary_route,
                       created_at, updated_at
                FROM onboarding_profiles
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        return OnboardingProfile(
            session_id=row["session_id"],
            primary_goal=row["primary_goal"],
            knowledge_level=row["knowledge_level"],
            risk_tolerance_prelim=row["risk_tolerance_prelim"],
            primary_interest=row["primary_interest"],
            current_state=row["current_state"],
            persona_segment=row["persona_segment"],
            guided_investing_eligible=bool(row["guided_investing_eligible"]),
            pro_eligible=bool(row["pro_eligible"]),
            primary_route=row["primary_route"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class SqliteHomeStateRepository(HomeStateRepository):
    def save(self, state: HomeState) -> HomeState:
        blocks_json = json.dumps(
            [
                {
                    "block_id": block.block_id,
                    "title": block.title,
                    "description": block.description,
                    "cta_label": block.cta_label,
                    "cta_path": block.cta_path,
                }
                for block in state.blocks
            ],
            ensure_ascii=False,
        )
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO home_states (
                    session_id, persona_segment, primary_route, next_best_action_type,
                    next_best_action_ref, trust_message, blocks_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    persona_segment = excluded.persona_segment,
                    primary_route = excluded.primary_route,
                    next_best_action_type = excluded.next_best_action_type,
                    next_best_action_ref = excluded.next_best_action_ref,
                    trust_message = excluded.trust_message,
                    blocks_json = excluded.blocks_json
                """,
                (
                    state.session_id,
                    state.persona_segment,
                    state.primary_route,
                    state.next_best_action_type,
                    state.next_best_action_ref,
                    state.trust_message,
                    blocks_json,
                ),
            )
            conn.commit()
        return state

    def get(self, session_id: str) -> HomeState | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT session_id, persona_segment, primary_route, next_best_action_type,
                       next_best_action_ref, trust_message, blocks_json
                FROM home_states
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        blocks = [
            HomeBlock(
                block_id=item["block_id"],
                title=item["title"],
                description=item["description"],
                cta_label=item.get("cta_label"),
                cta_path=item.get("cta_path"),
            )
            for item in json.loads(row["blocks_json"] or "[]")
        ]
        return HomeState(
            session_id=row["session_id"],
            persona_segment=row["persona_segment"],
            primary_route=row["primary_route"],
            next_best_action_type=row["next_best_action_type"],
            next_best_action_ref=row["next_best_action_ref"],
            trust_message=row["trust_message"],
            blocks=blocks,
        )


def reset_home_onboarding_state() -> None:
    reset_app_state_tables()
