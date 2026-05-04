from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from risk_dashboard.modules.financial_health.domain.entities import FinancialHealthSnapshot
from risk_dashboard.modules.goals.domain.entities import (
    Goal,
    GoalAction,
    GoalCheckIn,
    GoalPlannerReply,
    GoalReminderState,
    GoalSnapshot,
    utc_now_iso,
)


def _days_to_months(deadline: str) -> int:
    deadline_date = date.fromisoformat(deadline)
    days = max((deadline_date - datetime.now(timezone.utc).date()).days, 1)
    return max(1, round(days / 30))


def _goal_type_defaults(goal_type: str) -> tuple[str, str]:
    mapping = {
        "emergency_fund": ("medium", "cashflow-basics-101"),
        "home_purchase": ("high", "inflation-basics-101"),
        "education": ("high", "education-planning-101"),
        "wedding": ("medium", "budgeting-basics-101"),
        "retirement": ("high", "compounding-basics-101"),
        "travel": ("medium", "goal-savings-101"),
        "family_support": ("medium", "family-support-101"),
        "remittance": ("medium", "fx-basics-101"),
    }
    return mapping.get(goal_type, ("medium", "goal-savings-101"))


def create_goal(
    *,
    user_id: str,
    goal_type: str,
    goal_name: str,
    target_amount: float,
    current_amount: float,
    currency: str,
    base_currency: str,
    deadline: str,
    priority: str,
    confidence_level: str,
) -> Goal:
    return Goal(
        goal_id=str(uuid4()),
        user_id=user_id,
        goal_type=goal_type,
        goal_name=goal_name,
        target_amount=target_amount,
        current_amount=current_amount,
        currency=currency,
        base_currency=base_currency,
        deadline=deadline,
        priority=priority,
        confidence_level=confidence_level,
        status="active",
    )


def apply_checkin(goal: Goal, *, current_amount: float) -> Goal:
    status = "completed" if current_amount >= goal.target_amount else goal.status
    return replace(goal, current_amount=current_amount, status=status, updated_at=utc_now_iso())


def build_snapshot(goal: Goal, financial_health: FinancialHealthSnapshot | None) -> GoalSnapshot:
    gap_amount = round(max(goal.target_amount - goal.current_amount, 0.0), 2)
    months_remaining = _days_to_months(goal.deadline)
    monthly_contribution_needed = round(gap_amount / max(months_remaining, 1), 2)
    delay_3m_monthly_needed = round(gap_amount / max(months_remaining + 3, 1), 2)

    inflation_band, lesson_id = _goal_type_defaults(goal.goal_type)
    inflation_multiplier = {"low": 1.02, "medium": 1.05, "high": 1.08}[inflation_band]
    inflation_adjusted_target_estimate = round(goal.target_amount * inflation_multiplier, 2)

    is_multi_currency = goal.currency != goal.base_currency
    fx_sensitivity_band = "high" if is_multi_currency else "low"
    fx_upside_5pct_target = round(goal.target_amount * (1.05 if is_multi_currency else 1.0), 2)
    fx_downside_5pct_target = round(goal.target_amount * (0.95 if is_multi_currency else 1.0), 2)

    feasibility_band = _estimate_feasibility(goal, monthly_contribution_needed, months_remaining, financial_health)
    actions = _build_actions(goal, feasibility_band, financial_health)
    educational_links = [
        {"kind": "lesson", "id": lesson_id, "title": _lesson_title(lesson_id)},
        {"kind": "module", "id": "financial_health", "title": "Financial Health"},
    ]
    if feasibility_band in {"stretch", "high_stress", "not_feasible_yet"}:
        educational_links.append({"kind": "module", "id": "learning", "title": "Learn Hub"})
    return GoalSnapshot(
        goal_id=goal.goal_id,
        user_id=goal.user_id,
        gap_amount=gap_amount,
        months_remaining=months_remaining,
        monthly_contribution_needed=monthly_contribution_needed,
        feasibility_band=feasibility_band,
        delay_3m_monthly_needed=delay_3m_monthly_needed,
        inflation_sensitivity_band=inflation_band,
        inflation_adjusted_target_estimate=inflation_adjusted_target_estimate,
        fx_sensitivity_band=fx_sensitivity_band,
        fx_upside_5pct_target=fx_upside_5pct_target,
        fx_downside_5pct_target=fx_downside_5pct_target,
        actions=actions,
        educational_links=educational_links,
    )


def _estimate_feasibility(
    goal: Goal,
    monthly_contribution_needed: float,
    months_remaining: int,
    financial_health: FinancialHealthSnapshot | None,
) -> str:
    progress_ratio = goal.current_amount / goal.target_amount if goal.target_amount else 0
    if financial_health is not None:
        if financial_health.health_score < 40 or not financial_health.guided_investing_eligible and goal.goal_type != "emergency_fund":
            return "not_feasible_yet"
        if financial_health.health_score < 60:
            return "high_stress" if months_remaining < 12 else "stretch"
    if progress_ratio >= 0.5 and months_remaining >= 6:
        return "on_track"
    if months_remaining >= 12:
        return "stretch"
    if months_remaining >= 6:
        return "high_stress"
    if monthly_contribution_needed <= max(goal.target_amount * 0.03, 1):
        return "stretch"
    return "not_feasible_yet"


def _build_actions(
    goal: Goal,
    feasibility_band: str,
    financial_health: FinancialHealthSnapshot | None,
) -> list[GoalAction]:
    actions: list[GoalAction] = []
    if goal.goal_type == "emergency_fund":
        actions.append(
            GoalAction(
                code="track_cash_buffer",
                priority=1,
                title="Theo doi muc tich luy trong 2 tuan toi",
                description="Bat dau bang viec cap nhat so tien hien co deu dan.",
                cta_path="/goals",
            )
        )
    if feasibility_band in {"high_stress", "not_feasible_yet"}:
        actions.append(
            GoalAction(
                code="review_financial_health",
                priority=1,
                title="Quay lai Financial Health truoc",
                description="Nen tang dong tien va do an toan can chac hon de goal nay bot ap luc.",
                cta_path="/financial-health",
            )
        )
    if feasibility_band in {"stretch", "high_stress"}:
        actions.append(
            GoalAction(
                code="learn_tradeoffs",
                priority=2,
                title="Hoc bai ngan ve trade-off va ke hoach muc tieu",
                description="Mot bai hoc ngan giup ban hieu can doi giua deadline, muc tieu va su on dinh.",
                cta_path="/learn",
            )
        )
    if goal.goal_type == "remittance":
        actions.append(
            GoalAction(
                code="review_fx_buffer",
                priority=2,
                title="Them dem cho bien dong ty gia",
                description="Muc tieu da tien te nen co khoang dem nho cho FX sensitivity.",
                cta_path="/goals",
            )
        )
    if financial_health is not None and financial_health.guided_investing_eligible and goal.goal_type in {"retirement", "home_purchase"}:
        actions.append(
            GoalAction(
                code="explore_guided_investing",
                priority=3,
                title="Chi xem Guided Investing khi nen tang da on",
                description="Dung Guided Investing nhu cong cu giai thich va ho tro ke hoach dai han, khong phai tin hieu.",
                cta_path="/guide/watchlist",
            )
        )
    deduped: dict[str, GoalAction] = {}
    for action in actions:
        deduped[action.code] = action
    return sorted(deduped.values(), key=lambda item: item.priority)[:3]


def build_planner_reply(goal: Goal, snapshot: GoalSnapshot, financial_health: FinancialHealthSnapshot | None) -> GoalPlannerReply:
    band_copy = {
        "on_track": "Muc tieu nay hien dang o muc kha kha thi.",
        "stretch": "Muc tieu nay kha hop ly nhung se can ky luat deu dan.",
        "high_stress": "Muc tieu nay dang tao ap luc kha lon neu giu nguyen pace hien tai.",
        "not_feasible_yet": "Muc tieu nay chua nen day nhanh ngay luc nay.",
    }
    trade_offs = [
        f"Lui them 3 thang se giam muc dong gop moi thang xuong con {snapshot.delay_3m_monthly_needed:,.0f} {goal.currency}.",
        f"Neu tiep tuc voi deadline hien tai, ban can xap xi {snapshot.monthly_contribution_needed:,.0f} {goal.currency} moi thang.",
    ]
    if snapshot.fx_sensitivity_band == "high":
        trade_offs.append("Muc tieu nay nhay cam voi ty gia, nen co khoang dem nho thay vi lap ke hoach sat muc.")
    next_steps = [action.title for action in snapshot.actions]
    if not next_steps:
        next_steps = ["Cap nhat tien do goal nay hang tuan de tranh mat dau vet."]
    recommended_module = "financial_health" if financial_health is not None and financial_health.health_score < 60 else "learning"
    return GoalPlannerReply(
        summary=band_copy[snapshot.feasibility_band],
        feasibility_explanation=(
            f"Ban con thieu {snapshot.gap_amount:,.0f} {goal.currency} va con {snapshot.months_remaining} thang den deadline."
        ),
        trade_offs=trade_offs,
        next_steps=next_steps,
        recommended_module=recommended_module,
    )


def create_checkin(goal_id: str, *, current_amount: float, note: str | None) -> GoalCheckIn:
    return GoalCheckIn(
        checkin_id=str(uuid4()),
        goal_id=goal_id,
        current_amount=current_amount,
        note=note,
    )


def build_reminder_state(goal: Goal, snapshot: GoalSnapshot) -> GoalReminderState:
    status = _derive_reminder_status(goal, snapshot)
    frequency_days = {
        "off_track": 7,
        "due_soon": 7,
        "on_track": 14,
        "completed": 30,
    }[status]
    next_reminder_at = (datetime.now(timezone.utc) + timedelta(days=frequency_days)).isoformat()
    reminder_frequency = {
        "off_track": "weekly",
        "due_soon": "weekly",
        "on_track": "biweekly",
        "completed": "monthly",
    }[status]
    return GoalReminderState(
        goal_id=goal.goal_id,
        user_id=goal.user_id,
        reminder_frequency=reminder_frequency,
        last_status=status,
        next_reminder_at=next_reminder_at,
    )


def _derive_reminder_status(goal: Goal, snapshot: GoalSnapshot) -> str:
    if goal.status == "completed":
        return "completed"
    if snapshot.feasibility_band in {"high_stress", "not_feasible_yet"}:
        return "off_track"
    if snapshot.months_remaining <= 3:
        return "due_soon"
    return "on_track"


def _lesson_title(lesson_id: str) -> str:
    titles = {
        "cashflow-basics-101": "Dong tien co ban",
        "inflation-basics-101": "Lam phat anh huong den muc tieu the nao",
        "education-planning-101": "Lap muc tieu giao duc",
        "budgeting-basics-101": "Ngan sach va su kien lon",
        "compounding-basics-101": "Compounding basics",
        "goal-savings-101": "Tiet kiem theo muc tieu",
        "family-support-101": "Lap ke hoach ho tro gia dinh",
        "fx-basics-101": "FX basics cho muc tieu da tien te",
    }
    return titles.get(lesson_id, "Goal planning basics")
