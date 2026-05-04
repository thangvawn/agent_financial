from __future__ import annotations

import json

from risk_dashboard.modules.financial_health.domain.entities import FinancialHealthAction, FinancialHealthFlag, FinancialHealthSnapshot, FinancialHealthSubScore
from risk_dashboard.modules.goals.domain.entities import Goal, GoalAction, GoalCheckIn, GoalReminderState, GoalSnapshot
from risk_dashboard.modules.goals.domain.ports import (
    FinancialHealthReader,
    GoalCheckInRepository,
    GoalHomeReader,
    GoalReminderRepository,
    GoalRepository,
    GoalSnapshotRepository,
)
from risk_dashboard.platform.database import open_app_state_db, reset_app_state_tables


class SqliteGoalRepository(GoalRepository):
    def save(self, goal: Goal) -> Goal:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO goals (
                    goal_id, user_id, goal_type, goal_name, target_amount, current_amount,
                    currency, base_currency, deadline, priority, confidence_level, status,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(goal_id) DO UPDATE SET
                    user_id = excluded.user_id,
                    goal_type = excluded.goal_type,
                    goal_name = excluded.goal_name,
                    target_amount = excluded.target_amount,
                    current_amount = excluded.current_amount,
                    currency = excluded.currency,
                    base_currency = excluded.base_currency,
                    deadline = excluded.deadline,
                    priority = excluded.priority,
                    confidence_level = excluded.confidence_level,
                    status = excluded.status,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at
                """,
                (
                    goal.goal_id,
                    goal.user_id,
                    goal.goal_type,
                    goal.goal_name,
                    goal.target_amount,
                    goal.current_amount,
                    goal.currency,
                    goal.base_currency,
                    goal.deadline,
                    goal.priority,
                    goal.confidence_level,
                    goal.status,
                    goal.created_at,
                    goal.updated_at,
                ),
            )
            conn.commit()
        return goal

    def get(self, goal_id: str) -> Goal | None:
        with open_app_state_db() as conn:
            row = conn.execute("SELECT * FROM goals WHERE goal_id = ?", (goal_id,)).fetchone()
        if row is None:
            return None
        return Goal(**dict(row))

    def list_by_user(self, user_id: str) -> list[Goal]:
        with open_app_state_db() as conn:
            rows = conn.execute(
                "SELECT * FROM goals WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        return [Goal(**dict(row)) for row in rows]


class SqliteGoalSnapshotRepository(GoalSnapshotRepository):
    def save(self, snapshot: GoalSnapshot) -> GoalSnapshot:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO goal_snapshots (
                    goal_id, user_id, gap_amount, months_remaining, monthly_contribution_needed,
                    feasibility_band, delay_3m_monthly_needed, inflation_sensitivity_band,
                    inflation_adjusted_target_estimate, fx_sensitivity_band, fx_upside_5pct_target,
                    fx_downside_5pct_target, actions_json, educational_links_json, computed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(goal_id) DO UPDATE SET
                    user_id = excluded.user_id,
                    gap_amount = excluded.gap_amount,
                    months_remaining = excluded.months_remaining,
                    monthly_contribution_needed = excluded.monthly_contribution_needed,
                    feasibility_band = excluded.feasibility_band,
                    delay_3m_monthly_needed = excluded.delay_3m_monthly_needed,
                    inflation_sensitivity_band = excluded.inflation_sensitivity_band,
                    inflation_adjusted_target_estimate = excluded.inflation_adjusted_target_estimate,
                    fx_sensitivity_band = excluded.fx_sensitivity_band,
                    fx_upside_5pct_target = excluded.fx_upside_5pct_target,
                    fx_downside_5pct_target = excluded.fx_downside_5pct_target,
                    actions_json = excluded.actions_json,
                    educational_links_json = excluded.educational_links_json,
                    computed_at = excluded.computed_at
                """,
                (
                    snapshot.goal_id,
                    snapshot.user_id,
                    snapshot.gap_amount,
                    snapshot.months_remaining,
                    snapshot.monthly_contribution_needed,
                    snapshot.feasibility_band,
                    snapshot.delay_3m_monthly_needed,
                    snapshot.inflation_sensitivity_band,
                    snapshot.inflation_adjusted_target_estimate,
                    snapshot.fx_sensitivity_band,
                    snapshot.fx_upside_5pct_target,
                    snapshot.fx_downside_5pct_target,
                    json.dumps([item.__dict__ for item in snapshot.actions], ensure_ascii=False),
                    json.dumps(snapshot.educational_links, ensure_ascii=False),
                    snapshot.computed_at,
                ),
            )
            conn.commit()
        return snapshot

    def get(self, goal_id: str) -> GoalSnapshot | None:
        with open_app_state_db() as conn:
            row = conn.execute("SELECT * FROM goal_snapshots WHERE goal_id = ?", (goal_id,)).fetchone()
        if row is None:
            return None
        return GoalSnapshot(
            goal_id=row["goal_id"],
            user_id=row["user_id"],
            gap_amount=row["gap_amount"],
            months_remaining=row["months_remaining"],
            monthly_contribution_needed=row["monthly_contribution_needed"],
            feasibility_band=row["feasibility_band"],
            delay_3m_monthly_needed=row["delay_3m_monthly_needed"],
            inflation_sensitivity_band=row["inflation_sensitivity_band"],
            inflation_adjusted_target_estimate=row["inflation_adjusted_target_estimate"],
            fx_sensitivity_band=row["fx_sensitivity_band"],
            fx_upside_5pct_target=row["fx_upside_5pct_target"],
            fx_downside_5pct_target=row["fx_downside_5pct_target"],
            actions=[GoalAction(**item) for item in json.loads(row["actions_json"] or "[]")],
            educational_links=json.loads(row["educational_links_json"] or "[]"),
            computed_at=row["computed_at"],
        )

    def list_by_user(self, user_id: str) -> list[GoalSnapshot]:
        with open_app_state_db() as conn:
            rows = conn.execute(
                "SELECT * FROM goal_snapshots WHERE user_id = ? ORDER BY computed_at DESC",
                (user_id,),
            ).fetchall()
        return [
            GoalSnapshot(
                goal_id=row["goal_id"],
                user_id=row["user_id"],
                gap_amount=row["gap_amount"],
                months_remaining=row["months_remaining"],
                monthly_contribution_needed=row["monthly_contribution_needed"],
                feasibility_band=row["feasibility_band"],
                delay_3m_monthly_needed=row["delay_3m_monthly_needed"],
                inflation_sensitivity_band=row["inflation_sensitivity_band"],
                inflation_adjusted_target_estimate=row["inflation_adjusted_target_estimate"],
                fx_sensitivity_band=row["fx_sensitivity_band"],
                fx_upside_5pct_target=row["fx_upside_5pct_target"],
                fx_downside_5pct_target=row["fx_downside_5pct_target"],
                actions=[GoalAction(**item) for item in json.loads(row["actions_json"] or "[]")],
                educational_links=json.loads(row["educational_links_json"] or "[]"),
                computed_at=row["computed_at"],
            )
            for row in rows
        ]


class SqliteGoalCheckInRepository(GoalCheckInRepository):
    def save(self, checkin: GoalCheckIn) -> GoalCheckIn:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO goal_checkins (checkin_id, goal_id, current_amount, note, checked_in_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    checkin.checkin_id,
                    checkin.goal_id,
                    checkin.current_amount,
                    checkin.note,
                    checkin.checked_in_at,
                ),
            )
            conn.commit()
        return checkin


class SqliteGoalReminderRepository(GoalReminderRepository):
    def save(self, reminder: GoalReminderState) -> GoalReminderState:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO goal_reminder_states (
                    goal_id, user_id, reminder_frequency, last_status,
                    last_reminder_at, next_reminder_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(goal_id) DO UPDATE SET
                    user_id = excluded.user_id,
                    reminder_frequency = excluded.reminder_frequency,
                    last_status = excluded.last_status,
                    last_reminder_at = excluded.last_reminder_at,
                    next_reminder_at = excluded.next_reminder_at,
                    updated_at = excluded.updated_at
                """,
                (
                    reminder.goal_id,
                    reminder.user_id,
                    reminder.reminder_frequency,
                    reminder.last_status,
                    reminder.last_reminder_at,
                    reminder.next_reminder_at,
                    reminder.updated_at,
                ),
            )
            conn.commit()
        return reminder

    def get(self, goal_id: str) -> GoalReminderState | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                "SELECT * FROM goal_reminder_states WHERE goal_id = ?",
                (goal_id,),
            ).fetchone()
        if row is None:
            return None
        return GoalReminderState(
            goal_id=row["goal_id"],
            user_id=row["user_id"],
            reminder_frequency=row["reminder_frequency"],
            last_status=row["last_status"],
            next_reminder_at=row["next_reminder_at"],
            last_reminder_at=row["last_reminder_at"],
            updated_at=row["updated_at"],
        )


class SqliteGoalHomeReader(GoalHomeReader):
    def get_latest_goal_summary(self, user_id: str) -> tuple[Goal, GoalSnapshot] | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT
                    g.goal_id,
                    g.user_id,
                    g.goal_type,
                    g.goal_name,
                    g.target_amount,
                    g.current_amount,
                    g.currency,
                    g.base_currency,
                    g.deadline,
                    g.priority,
                    g.confidence_level,
                    g.status,
                    g.created_at,
                    g.updated_at,
                    s.gap_amount,
                    s.months_remaining,
                    s.monthly_contribution_needed,
                    s.feasibility_band,
                    s.delay_3m_monthly_needed,
                    s.inflation_sensitivity_band,
                    s.inflation_adjusted_target_estimate,
                    s.fx_sensitivity_band,
                    s.fx_upside_5pct_target,
                    s.fx_downside_5pct_target,
                    s.actions_json,
                    s.educational_links_json,
                    s.computed_at
                FROM goals g
                JOIN goal_snapshots s ON s.goal_id = g.goal_id
                WHERE g.user_id = ?
                ORDER BY g.updated_at DESC, g.created_at DESC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
        if row is None:
            return None
        goal = Goal(
            goal_id=row["goal_id"],
            user_id=row["user_id"],
            goal_type=row["goal_type"],
            goal_name=row["goal_name"],
            target_amount=row["target_amount"],
            current_amount=row["current_amount"],
            currency=row["currency"],
            base_currency=row["base_currency"],
            deadline=row["deadline"],
            priority=row["priority"],
            confidence_level=row["confidence_level"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        snapshot = GoalSnapshot(
            goal_id=row["goal_id"],
            user_id=row["user_id"],
            gap_amount=row["gap_amount"],
            months_remaining=row["months_remaining"],
            monthly_contribution_needed=row["monthly_contribution_needed"],
            feasibility_band=row["feasibility_band"],
            delay_3m_monthly_needed=row["delay_3m_monthly_needed"],
            inflation_sensitivity_band=row["inflation_sensitivity_band"],
            inflation_adjusted_target_estimate=row["inflation_adjusted_target_estimate"],
            fx_sensitivity_band=row["fx_sensitivity_band"],
            fx_upside_5pct_target=row["fx_upside_5pct_target"],
            fx_downside_5pct_target=row["fx_downside_5pct_target"],
            actions=[GoalAction(**item) for item in json.loads(row["actions_json"] or "[]")],
            educational_links=json.loads(row["educational_links_json"] or "[]"),
            computed_at=row["computed_at"],
        )
        return goal, snapshot


class SqliteFinancialHealthReader(FinancialHealthReader):
    def get(self, session_id: str) -> FinancialHealthSnapshot | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                "SELECT * FROM financial_health_snapshots WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        return FinancialHealthSnapshot(
            session_id=row["session_id"],
            health_score=row["health_score"],
            score_band=row["score_band"],
            guided_investing_eligible=bool(row["guided_investing_eligible"]),
            subscores=[FinancialHealthSubScore(**item) for item in json.loads(row["subscores_json"] or "[]")],
            flags=[FinancialHealthFlag(**item) for item in json.loads(row["flags_json"] or "[]")],
            actions=[FinancialHealthAction(**item) for item in json.loads(row["actions_json"] or "[]")],
            educational_links=json.loads(row["educational_links_json"] or "[]"),
            transparency_note=row["transparency_note"],
            compliance_note=row["compliance_note"],
            computed_at=row["computed_at"],
        )


def reset_goals_state() -> None:
    reset_app_state_tables()
