from __future__ import annotations

import json

from risk_dashboard.modules.financial_health.domain.entities import (
    FinancialHealthAction,
    FinancialHealthFlag,
    FinancialHealthInput,
    FinancialHealthSnapshot,
    FinancialHealthSubScore,
)
from risk_dashboard.modules.financial_health.domain.ports import (
    FinancialHealthInputRepository,
    FinancialHealthSnapshotRepository,
)
from risk_dashboard.platform.database import open_app_state_db, reset_app_state_tables


class SqliteFinancialHealthInputRepository(FinancialHealthInputRepository):
    def save(self, payload: FinancialHealthInput) -> FinancialHealthInput:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO financial_health_inputs (
                    session_id, monthly_income_range, income_stability_level, expense_discipline_level,
                    emergency_fund_months_band, monthly_debt_payment_ratio_band, savings_rate_band,
                    liquidity_stress_level, has_basic_insurance, has_high_interest_debt,
                    wants_to_start_investing, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    monthly_income_range = excluded.monthly_income_range,
                    income_stability_level = excluded.income_stability_level,
                    expense_discipline_level = excluded.expense_discipline_level,
                    emergency_fund_months_band = excluded.emergency_fund_months_band,
                    monthly_debt_payment_ratio_band = excluded.monthly_debt_payment_ratio_band,
                    savings_rate_band = excluded.savings_rate_band,
                    liquidity_stress_level = excluded.liquidity_stress_level,
                    has_basic_insurance = excluded.has_basic_insurance,
                    has_high_interest_debt = excluded.has_high_interest_debt,
                    wants_to_start_investing = excluded.wants_to_start_investing,
                    created_at = excluded.created_at
                """,
                (
                    payload.session_id,
                    payload.monthly_income_range,
                    payload.income_stability_level,
                    payload.expense_discipline_level,
                    payload.emergency_fund_months_band,
                    payload.monthly_debt_payment_ratio_band,
                    payload.savings_rate_band,
                    payload.liquidity_stress_level,
                    int(payload.has_basic_insurance),
                    int(payload.has_high_interest_debt),
                    int(payload.wants_to_start_investing),
                    payload.created_at,
                ),
            )
            conn.commit()
        return payload

    def get(self, session_id: str) -> FinancialHealthInput | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT session_id, monthly_income_range, income_stability_level, expense_discipline_level,
                       emergency_fund_months_band, monthly_debt_payment_ratio_band, savings_rate_band,
                       liquidity_stress_level, has_basic_insurance, has_high_interest_debt,
                       wants_to_start_investing, created_at
                FROM financial_health_inputs
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        return FinancialHealthInput(
            session_id=row["session_id"],
            monthly_income_range=row["monthly_income_range"],
            income_stability_level=row["income_stability_level"],
            expense_discipline_level=row["expense_discipline_level"],
            emergency_fund_months_band=row["emergency_fund_months_band"],
            monthly_debt_payment_ratio_band=row["monthly_debt_payment_ratio_band"],
            savings_rate_band=row["savings_rate_band"],
            liquidity_stress_level=row["liquidity_stress_level"],
            has_basic_insurance=bool(row["has_basic_insurance"]),
            has_high_interest_debt=bool(row["has_high_interest_debt"]),
            wants_to_start_investing=bool(row["wants_to_start_investing"]),
            created_at=row["created_at"],
        )


class SqliteFinancialHealthSnapshotRepository(FinancialHealthSnapshotRepository):
    def save(self, snapshot: FinancialHealthSnapshot) -> FinancialHealthSnapshot:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO financial_health_snapshots (
                    session_id, health_score, score_band, guided_investing_eligible, subscores_json,
                    flags_json, actions_json, educational_links_json, transparency_note,
                    compliance_note, computed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    health_score = excluded.health_score,
                    score_band = excluded.score_band,
                    guided_investing_eligible = excluded.guided_investing_eligible,
                    subscores_json = excluded.subscores_json,
                    flags_json = excluded.flags_json,
                    actions_json = excluded.actions_json,
                    educational_links_json = excluded.educational_links_json,
                    transparency_note = excluded.transparency_note,
                    compliance_note = excluded.compliance_note,
                    computed_at = excluded.computed_at
                """,
                (
                    snapshot.session_id,
                    snapshot.health_score,
                    snapshot.score_band,
                    int(snapshot.guided_investing_eligible),
                    json.dumps([item.__dict__ for item in snapshot.subscores], ensure_ascii=False),
                    json.dumps([item.__dict__ for item in snapshot.flags], ensure_ascii=False),
                    json.dumps([item.__dict__ for item in snapshot.actions], ensure_ascii=False),
                    json.dumps(snapshot.educational_links, ensure_ascii=False),
                    snapshot.transparency_note,
                    snapshot.compliance_note,
                    snapshot.computed_at,
                ),
            )
            conn.commit()
        return snapshot

    def get(self, session_id: str) -> FinancialHealthSnapshot | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT session_id, health_score, score_band, guided_investing_eligible, subscores_json,
                       flags_json, actions_json, educational_links_json, transparency_note,
                       compliance_note, computed_at
                FROM financial_health_snapshots
                WHERE session_id = ?
                """,
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


def reset_financial_health_state() -> None:
    reset_app_state_tables()
