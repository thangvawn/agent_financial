"""Baseline regression tests for legacy goals module.
Captures current behavior WITHOUT HTTP (router unmounted).
Serves as behavioral contract that must not regress before reactivation.
"""
from __future__ import annotations

import pytest

from risk_dashboard.modules.goals.domain.entities import Goal, utc_now_iso
from risk_dashboard.modules.goals.domain.policies import (
    _days_to_months,
    _goal_type_defaults,
    apply_checkin,
    build_planner_reply,
    build_reminder_state,
    build_snapshot,
    create_checkin,
    create_goal,
)
from risk_dashboard.modules.goals.schemas.requests import GoalCheckInRequest, GoalCreateRequest
from risk_dashboard.modules.goals.schemas.responses import (
    GoalActionResponse,
    GoalPlannerResponse,
    GoalResponse,
    GoalSummaryResponse,
)


def _make_goal(**overrides) -> Goal:
    base = dict(
        user_id="session-baseline-001",
        goal_type="emergency_fund",
        goal_name="Quy du phong 1 thang",
        target_amount=20000000.0,
        current_amount=2000000.0,
        currency="VND",
        base_currency="VND",
        deadline="2027-01-31",
        priority="high",
        confidence_level="estimated",
    )
    base.update(overrides)
    return create_goal(**base)


class TestGoalsBaseline:
    def test_create_goal_entity(self) -> None:
        goal = _make_goal()
        assert goal.goal_id
        assert goal.user_id == "session-baseline-001"
        assert goal.goal_type == "emergency_fund"
        assert goal.status == "active"
        assert goal.target_amount == 20000000.0
        assert goal.current_amount == 2000000.0
        assert goal.created_at
        assert goal.updated_at

    def test_build_snapshot_metrics(self) -> None:
        goal = _make_goal()
        snap = build_snapshot(goal, financial_health=None)
        assert snap.gap_amount == 18000000.0
        assert snap.months_remaining >= 1
        assert snap.monthly_contribution_needed > 0
        assert snap.feasibility_band in {"on_track", "stretch", "high_stress", "not_feasible_yet"}
        assert snap.inflation_sensitivity_band == "medium"  # emergency_fund default
        assert snap.fx_sensitivity_band == "low"  # VND/VND same currency
        assert snap.actions
        assert len(snap.educational_links) >= 1

    def test_apply_checkin_completes_goal(self) -> None:
        goal = _make_goal(current_amount=2000000.0)
        # Update with amount equal to target
        updated = apply_checkin(goal, current_amount=20000000.0)
        assert updated.status == "completed"
        assert updated.current_amount == 20000000.0

    def test_apply_checkin_partial_progress(self) -> None:
        goal = _make_goal(current_amount=2000000.0)
        updated = apply_checkin(goal, current_amount=5000000.0)
        assert updated.status == "active"
        assert updated.current_amount == 5000000.0

    def test_create_checkin_record(self) -> None:
        checkin = create_checkin("goal-123", current_amount=5000000.0, note="Tiet kiem thang 1")
        assert checkin.checkin_id
        assert checkin.goal_id == "goal-123"
        assert checkin.current_amount == 5000000.0
        assert checkin.note == "Tiet kiem thang 1"
        assert checkin.checked_in_at

    def test_build_planner_reply(self) -> None:
        goal = _make_goal()
        snap = build_snapshot(goal, financial_health=None)
        reply = build_planner_reply(goal, snap, financial_health=None)
        assert reply.summary
        assert reply.feasibility_explanation
        assert reply.trade_offs
        assert reply.next_steps
        assert reply.recommended_module in {"learning", "financial_health", "goals"}

    def test_build_reminder_state(self) -> None:
        goal = _make_goal()
        snap = build_snapshot(goal, financial_health=None)
        state = build_reminder_state(goal, snap)
        assert state.reminder_frequency in {"weekly", "biweekly", "monthly"}
        assert state.last_status in {"on_track", "due_soon", "off_track", "completed"}
        assert state.next_reminder_at

    def test_goal_create_request_schema(self) -> None:
        req = GoalCreateRequest(
            session_id="session-baseline-001",
            goal_type="emergency_fund",
            goal_name="Test Goal",
            deadline="2027-01-31",
            target_amount=10000000,
            current_amount=0,
            priority="high",
            currency="VND",
            base_currency="VND",
            confidence_level="estimated",
        )
        assert req.session_id == "session-baseline-001"
        assert req.target_amount == 10000000

    def test_goal_response_schema_roundtrip(self) -> None:
        goal = _make_goal()
        snap = build_snapshot(goal, financial_health=None)
        resp = GoalResponse(
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
            gap_amount=snap.gap_amount,
            months_remaining=snap.months_remaining,
            monthly_contribution_needed=snap.monthly_contribution_needed,
            feasibility_band=snap.feasibility_band,
            delay_3m_monthly_needed=snap.delay_3m_monthly_needed,
            inflation_sensitivity_band=snap.inflation_sensitivity_band,
            inflation_adjusted_target_estimate=snap.inflation_adjusted_target_estimate,
            fx_sensitivity_band=snap.fx_sensitivity_band,
            fx_upside_5pct_target=snap.fx_upside_5pct_target,
            fx_downside_5pct_target=snap.fx_downside_5pct_target,
            reminder_status="on_track",
            next_reminder_at="2027-02-01T00:00:00Z",
            actions=[
                GoalActionResponse(
                    code=item.code,
                    priority=item.priority,
                    title=item.title,
                    description=item.description,
                    cta_path=item.cta_path,
                )
                for item in snap.actions
            ],
            educational_links=snap.educational_links,
        )
        assert resp.goal_id == goal.goal_id
        assert resp.user_id == goal.user_id
        assert resp.gap_amount == 18000000.0

    def test_goal_type_defaults(self) -> None:
        band, lesson = _goal_type_defaults("emergency_fund")
        assert band == "medium"
        assert lesson == "cashflow-basics-101"

        band_home, lesson_home = _goal_type_defaults("home_purchase")
        assert band_home == "high"
        assert lesson_home == "inflation-basics-101"

        band_unk, lesson_unk = _goal_type_defaults("unknown_custom_goal")
        assert band_unk == "medium"
        assert lesson_unk == "goal-savings-101"

    def test_goal_multi_currency_fx_sensitivity(self) -> None:
        goal = _make_goal(currency="USD", base_currency="VND")
        snap = build_snapshot(goal, financial_health=None)
        assert snap.fx_sensitivity_band == "high"
        assert snap.fx_upside_5pct_target == round(20000000.0 * 1.05, 2)
        assert snap.fx_downside_5pct_target == round(20000000.0 * 0.95, 2)

