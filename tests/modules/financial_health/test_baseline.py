"""Baseline regression tests for legacy financial_health module.
Captures current behavior WITHOUT HTTP (router unmounted).
Serves as behavioral contract that must not regress before reactivation.
"""
from __future__ import annotations

import pytest

from risk_dashboard.modules.financial_health.domain.entities import (
    FinancialHealthAction,
    FinancialHealthFlag,
    FinancialHealthInput,
    FinancialHealthSnapshot,
    FinancialHealthSubScore,
)
from risk_dashboard.modules.financial_health.domain.policies import (
    _WEIGHTS,
    _score_band,
    build_actions,
    build_coach_reply,
    build_flags,
    build_snapshot,
    compute_subscores,
)
from risk_dashboard.modules.financial_health.schemas.requests import FinancialHealthAssessmentRequest
from risk_dashboard.modules.financial_health.schemas.responses import (
    FinancialHealthCoachResponse,
    FinancialHealthResponse,
)


def _make_input(**overrides) -> FinancialHealthInput:
    base = dict(
        session_id="session-fh-baseline-001",
        monthly_income_range="mid",
        income_stability_level="stable",
        expense_discipline_level="mostly_disciplined",
        emergency_fund_months_band="1_to_3m",
        monthly_debt_payment_ratio_band="10_to_30pct",
        savings_rate_band="10_to_20pct",
        liquidity_stress_level="rare",
        has_basic_insurance=True,
        has_high_interest_debt=False,
        wants_to_start_investing=True,
        created_at="2026-09-05T10:00:00Z",
    )
    base.update(overrides)
    return FinancialHealthInput(**base)


class TestFinancialHealthBaseline:
    def test_subscores_weights_sum_to_one(self) -> None:
        total_weight = sum(_WEIGHTS.values())
        assert pytest.approx(total_weight, rel=1e-5) == 1.0
        assert len(_WEIGHTS) == 8

    def test_compute_subscores_8_categories(self) -> None:
        payload = _make_input()
        subscores = compute_subscores(payload)
        assert len(subscores) == 8
        keys = {s.key for s in subscores}
        expected_keys = {
            "income_stability",
            "expense_discipline",
            "emergency_fund",
            "debt_load",
            "savings_rate",
            "liquidity_stress",
            "protection_basics",
            "investment_readiness",
        }
        assert keys == expected_keys
        for s in subscores:
            assert 0 <= s.score <= 100
            assert s.label
            assert s.reason
            assert s.improvement_hint

    def test_score_band_derivation(self) -> None:
        assert _score_band(30) == "needs_stabilization"
        assert _score_band(55) == "fragile_foundation"
        assert _score_band(75) == "building_strength"
        assert _score_band(90) == "healthy_foundation"

    def test_build_snapshot_high_quality_profile(self) -> None:
        payload = _make_input(
            income_stability_level="stable",
            expense_discipline_level="disciplined",
            emergency_fund_months_band="3_to_6m",
            monthly_debt_payment_ratio_band="lt_10pct",
            savings_rate_band="20_to_30pct",
            liquidity_stress_level="comfortable",
            has_basic_insurance=True,
            has_high_interest_debt=False,
            wants_to_start_investing=True,
        )
        snapshot = build_snapshot(payload)
        assert snapshot.health_score >= 70
        assert snapshot.score_band in {"building_strength", "healthy_foundation"}
        assert snapshot.guided_investing_eligible is True
        assert snapshot.transparency_note
        assert snapshot.compliance_note
        assert snapshot.computed_at

    def test_build_snapshot_risky_profile_blocks_guided_investing(self) -> None:
        payload = _make_input(
            emergency_fund_months_band="none",
            monthly_debt_payment_ratio_band="gt_50pct",
            has_high_interest_debt=True,
            has_basic_insurance=False,
            income_stability_level="unstable",
        )
        snapshot = build_snapshot(payload)
        assert snapshot.guided_investing_eligible is False
        assert snapshot.health_score < 60
        assert any(f.code == "low_emergency_buffer" for f in snapshot.flags)
        assert any(a.code == "start_emergency_fund_goal" for a in snapshot.actions)

    def test_build_coach_reply_general(self) -> None:
        payload = _make_input()
        snapshot = build_snapshot(payload)
        reply = build_coach_reply(snapshot, focus=None)
        assert reply.summary
        assert reply.explanation
        assert reply.next_small_actions
        assert reply.confidence_note

    def test_build_coach_reply_with_focus(self) -> None:
        payload = _make_input()
        snapshot = build_snapshot(payload)
        reply = build_coach_reply(snapshot, focus="investment_readiness")
        assert reply.summary
        assert "investment" in reply.explanation.lower() or "đầu tư" in reply.explanation.lower()

    def test_assessment_request_schema(self) -> None:
        req = FinancialHealthAssessmentRequest(
            session_id="session-fh-baseline-001",
            monthly_income_range="mid",
            income_stability_level="mostly_stable",
            expense_discipline_level="mostly_disciplined",
            emergency_fund_months_band="1_to_3m",
            monthly_debt_payment_ratio_band="10_to_30pct",
            savings_rate_band="10_to_20pct",
            liquidity_stress_level="rare",
            has_basic_insurance=True,
            has_high_interest_debt=False,
            wants_to_start_investing=True,
        )
        assert req.session_id == "session-fh-baseline-001"
        assert req.has_basic_insurance is True

    def test_financial_health_response_schema_roundtrip(self) -> None:
        payload = _make_input()
        snapshot = build_snapshot(payload)
        resp = FinancialHealthResponse(
            session_id=snapshot.session_id,
            health_score=snapshot.health_score,
            score_band=snapshot.score_band,
            guided_investing_eligible=snapshot.guided_investing_eligible,
            subscores=[
                {
                    "key": item.key,
                    "label": item.label,
                    "score": item.score,
                    "reason": item.reason,
                    "improvement_hint": item.improvement_hint,
                }
                for item in snapshot.subscores
            ],
            flags=[
                {
                    "code": item.code,
                    "severity": item.severity,
                    "title": item.title,
                    "description": item.description,
                }
                for item in snapshot.flags
            ],
            actions=[
                {
                    "code": item.code,
                    "priority": item.priority,
                    "title": item.title,
                    "description": item.description,
                    "related_lesson_id": item.related_lesson_id,
                    "cta_path": item.cta_path,
                }
                for item in snapshot.actions
            ],
            educational_links=snapshot.educational_links,
            transparency_note=snapshot.transparency_note,
            compliance_note=snapshot.compliance_note,
            computed_at=snapshot.computed_at,
        )
        assert resp.session_id == snapshot.session_id
        assert resp.health_score == snapshot.health_score
        assert len(resp.subscores) == 8

