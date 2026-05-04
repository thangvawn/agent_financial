from __future__ import annotations

from risk_dashboard.modules.analytics_monitoring.application.emitter import emit_product_event
from risk_dashboard.modules.goals.domain.policies import (
    apply_checkin,
    build_planner_reply,
    build_reminder_state,
    build_snapshot,
    create_checkin,
    create_goal,
)
from risk_dashboard.modules.goals.domain.ports import (
    FinancialHealthReader,
    GoalCheckInRepository,
    GoalReminderRepository,
    GoalRepository,
    GoalSnapshotRepository,
)
from risk_dashboard.modules.goals.schemas.requests import GoalCheckInRequest, GoalCreateRequest
from risk_dashboard.modules.goals.schemas.responses import GoalPlannerResponse, GoalResponse, GoalSummaryResponse


class CreateGoal:
    def __init__(
        self,
        goals: GoalRepository,
        snapshots: GoalSnapshotRepository,
        financial_health: FinancialHealthReader,
        reminders: GoalReminderRepository,
    ) -> None:
        self.goals = goals
        self.snapshots = snapshots
        self.financial_health = financial_health
        self.reminders = reminders

    def execute(self, req: GoalCreateRequest) -> GoalResponse:
        goal = create_goal(
            user_id=req.session_id,
            goal_type=req.goal_type,
            goal_name=req.goal_name,
            target_amount=req.target_amount,
            current_amount=req.current_amount,
            currency=req.currency,
            base_currency=req.base_currency,
            deadline=req.deadline,
            priority=req.priority,
            confidence_level=req.confidence_level,
        )
        goal = self.goals.save(goal)
        snapshot = self.snapshots.save(build_snapshot(goal, self.financial_health.get(req.session_id)))
        reminder = self.reminders.save(build_reminder_state(goal, snapshot))
        emit_product_event(
            event_name="goal_created",
            module="goals",
            surface="goals",
            session_id=req.session_id,
            properties={
                "goal_id": goal.goal_id,
                "goal_type": goal.goal_type,
                "feasibility_band": snapshot.feasibility_band,
                "currency": goal.currency,
            },
        )
        return _to_response(goal, snapshot, reminder)


class ListGoals:
    def __init__(
        self,
        goals: GoalRepository,
        snapshots: GoalSnapshotRepository,
        reminders: GoalReminderRepository,
    ) -> None:
        self.goals = goals
        self.snapshots = snapshots
        self.reminders = reminders

    def execute(self, *, user_id: str) -> list[GoalSummaryResponse]:
        goals = self.goals.list_by_user(user_id)
        snapshots = {item.goal_id: item for item in self.snapshots.list_by_user(user_id)}
        reminders = {goal.goal_id: self.reminders.get(goal.goal_id) for goal in goals}
        return [
            GoalSummaryResponse(
                goal_id=goal.goal_id,
                goal_name=goal.goal_name,
                goal_type=goal.goal_type,
                target_amount=goal.target_amount,
                current_amount=goal.current_amount,
                currency=goal.currency,
                feasibility_band=snapshots[goal.goal_id].feasibility_band,
                monthly_contribution_needed=snapshots[goal.goal_id].monthly_contribution_needed,
                reminder_status=reminders[goal.goal_id].last_status if reminders[goal.goal_id] is not None else None,
                next_reminder_at=reminders[goal.goal_id].next_reminder_at if reminders[goal.goal_id] is not None else None,
            )
            for goal in goals
            if goal.goal_id in snapshots
        ]


class GetGoal:
    def __init__(
        self,
        goals: GoalRepository,
        snapshots: GoalSnapshotRepository,
        reminders: GoalReminderRepository,
    ) -> None:
        self.goals = goals
        self.snapshots = snapshots
        self.reminders = reminders

    def execute(self, *, goal_id: str) -> GoalResponse:
        goal = self.goals.get(goal_id)
        snapshot = self.snapshots.get(goal_id)
        if goal is None or snapshot is None:
            raise ValueError("Goal not found.")
        return _to_response(goal, snapshot, self.reminders.get(goal_id))


class RecordGoalCheckIn:
    def __init__(
        self,
        goals: GoalRepository,
        snapshots: GoalSnapshotRepository,
        checkins: GoalCheckInRepository,
        financial_health: FinancialHealthReader,
        reminders: GoalReminderRepository,
    ) -> None:
        self.goals = goals
        self.snapshots = snapshots
        self.checkins = checkins
        self.financial_health = financial_health
        self.reminders = reminders

    def execute(self, *, goal_id: str, req: GoalCheckInRequest) -> GoalResponse:
        goal = self.goals.get(goal_id)
        if goal is None:
            raise ValueError("Goal not found.")
        goal = self.goals.save(apply_checkin(goal, current_amount=req.current_amount))
        self.checkins.save(create_checkin(goal_id, current_amount=req.current_amount, note=req.note))
        snapshot = self.snapshots.save(build_snapshot(goal, self.financial_health.get(goal.user_id)))
        reminder = self.reminders.save(build_reminder_state(goal, snapshot))
        emit_product_event(
            event_name="goal_checkin_completed",
            module="goals",
            surface="goals",
            user_id=goal.user_id,
            session_id=goal.user_id,
            properties={
                "goal_id": goal.goal_id,
                "current_amount": goal.current_amount,
                "feasibility_band": snapshot.feasibility_band,
            },
        )
        return _to_response(goal, snapshot, reminder)


class ExplainGoalPlan:
    def __init__(
        self,
        goals: GoalRepository,
        snapshots: GoalSnapshotRepository,
        financial_health: FinancialHealthReader,
    ) -> None:
        self.goals = goals
        self.snapshots = snapshots
        self.financial_health = financial_health

    def execute(self, *, goal_id: str) -> GoalPlannerResponse:
        goal = self.goals.get(goal_id)
        snapshot = self.snapshots.get(goal_id)
        if goal is None or snapshot is None:
            raise ValueError("Goal not found.")
        reply = build_planner_reply(goal, snapshot, self.financial_health.get(goal.user_id))
        emit_product_event(
            event_name="goal_planner_opened",
            module="goals",
            surface="goals",
            user_id=goal.user_id,
            session_id=goal.user_id,
            properties={"goal_id": goal_id, "recommended_module": reply.recommended_module},
        )
        return GoalPlannerResponse(
            goal_id=goal_id,
            summary=reply.summary,
            feasibility_explanation=reply.feasibility_explanation,
            trade_offs=reply.trade_offs,
            next_steps=reply.next_steps,
            recommended_module=reply.recommended_module,
        )


def _to_response(goal, snapshot, reminder=None) -> GoalResponse:
    return GoalResponse(
        goal_id=goal.goal_id,
        user_id=goal.user_id,
        goal_type=goal.goal_type,
        goal_name=goal.goal_name,
        target_amount=goal.target_amount,
        current_amount=goal.current_amount,
        currency=goal.currency,
        base_currency=goal.base_currency,
        deadline=goal.deadline,
        priority=goal.priority,
        confidence_level=goal.confidence_level,
        status=goal.status,
        gap_amount=snapshot.gap_amount,
        months_remaining=snapshot.months_remaining,
        monthly_contribution_needed=snapshot.monthly_contribution_needed,
        feasibility_band=snapshot.feasibility_band,
        delay_3m_monthly_needed=snapshot.delay_3m_monthly_needed,
        inflation_sensitivity_band=snapshot.inflation_sensitivity_band,
        inflation_adjusted_target_estimate=snapshot.inflation_adjusted_target_estimate,
        fx_sensitivity_band=snapshot.fx_sensitivity_band,
        fx_upside_5pct_target=snapshot.fx_upside_5pct_target,
        fx_downside_5pct_target=snapshot.fx_downside_5pct_target,
        reminder_status=reminder.last_status if reminder is not None else None,
        next_reminder_at=reminder.next_reminder_at if reminder is not None else None,
        actions=[
            {
                "code": item.code,
                "priority": item.priority,
                "title": item.title,
                "description": item.description,
                "cta_path": item.cta_path,
            }
            for item in snapshot.actions
        ],
        educational_links=snapshot.educational_links,
    )
