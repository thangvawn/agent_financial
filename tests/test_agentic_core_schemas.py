from __future__ import annotations

import pytest
from pydantic import ValidationError

from risk_dashboard.modules.agentic_core.schemas.artifact import ActionProposal, ActionReceipt, AgentArtifact
from risk_dashboard.modules.agentic_core.schemas.claim import (
    Claim,
    ClaimKind,
    ClaimLedger,
    ClaimStatus,
    ReviewedArtifact,
    ReviewedClaim,
)
from risk_dashboard.modules.agentic_core.schemas.envelope import (
    ExecutionBudget,
    ResourceRef,
    TrustedExecutionEnvelope,
)
from risk_dashboard.modules.agentic_core.schemas.memory import MemoryProposal
from risk_dashboard.modules.agentic_core.schemas.requests import AgentRunRequestV1, AgentRunResponseV1
from risk_dashboard.modules.agentic_core.schemas.runs import AgentRun, AgentStep, ToolCallRecord
from risk_dashboard.modules.auth.schemas.principal import ConsentSnapshot

NOW = "2026-08-28T12:00:00+00:00"


def test_agentic_schemas_round_trip() -> None:
    resource = ResourceRef(kind="report", resource_id="report-1", module="pro_lab")
    envelope = TrustedExecutionEnvelope(
        run_id="run-1",
        correlation_id="correlation-1",
        idempotency_key="idempotency-1",
        account_id="account-a",
        surface="pro_lab",
        resource_refs=(resource,),
        budget=ExecutionBudget(),
        policy_version="v1",
        model_policy_version="v1",
        consent=ConsentSnapshot(policy_version="v1"),
        created_at=NOW,
    )
    artifact = AgentArtifact(
        artifact_id="artifact-1",
        artifact_type="analysis",
        domain="finance",
        account_id="account-a",
        authoring_run_id="run-1",
        created_at=NOW,
    )
    proposal = ActionProposal(
        proposal_id="proposal-1",
        run_id="run-1",
        account_id="account-a",
        operation="export_report",
        target=resource,
        payload_preview={},
        risk_class="proposal",
        policy_version="v1",
        created_at=NOW,
        expires_at=NOW,
    )
    receipt = ActionReceipt(
        receipt_id="rcpt-1",
        proposal_id="proposal-1",
        account_id="account-a",
        status="executed",
        executed_at=NOW,
    )
    memory = MemoryProposal(
        proposal_id="memory-1",
        run_id="run-1",
        account_id="account-a",
        memory_type="goal",
        content="Learn valuation",
        provenance="user_stated",
        created_at=NOW,
    )
    run = AgentRun(
        run_id="run-1",
        account_id="account-a",
        surface="pro_lab",
        status="accepted",
        created_at=NOW,
        updated_at=NOW,
    )
    step = AgentStep(
        step_id="step-1",
        run_id="run-1",
        step_index=0,
        agent_id="supervisor",
        node_name="guard_node",
        status="completed",
        started_at=NOW,
    )
    tool_call = ToolCallRecord(
        tool_call_id="tc-1",
        run_id="run-1",
        account_id="account-a",
        tool_name="quant.var",
        input_hash="hash-123",
        status="success",
        created_at=NOW,
    )
    request = AgentRunRequestV1(
        operation="analyze_risk",
        surface="pro_lab",
        resource_refs=(resource,),
    )
    response = AgentRunResponseV1(
        run_id="run-1",
        status="completed",
        artifact=artifact,
        action_proposal=proposal,
    )

    for model in (envelope, artifact, proposal, receipt, memory, run, step, tool_call, request, response):
        assert type(model).model_validate_json(model.model_dump_json()) == model
        assert getattr(model, "schema_version") == "1.0.0"


def test_schema_extra_fields_forbidden() -> None:
    """Iron Rule 4: Cấm Extra Fields."""
    with pytest.raises(ValidationError):
        ResourceRef(kind="report", resource_id="r1", module="pro_lab", injected_field="malicious")  # type: ignore

    with pytest.raises(ValidationError):
        ExecutionBudget(max_steps=8, extra_step=10)  # type: ignore

    with pytest.raises(ValidationError):
        ActionReceipt(
            receipt_id="r-1",
            proposal_id="p-1",
            account_id="a-1",
            status="executed",
            executed_at=NOW,
            unauthorized_data="leak",  # type: ignore
        )


def test_client_cannot_inject_authority_fields_in_request() -> None:
    """Client request schema AgentRunRequestV1 must reject account_id/scopes injection."""
    # Valid client request
    req = AgentRunRequestV1(
        operation="analyze_risk",
        surface="pro_lab",
        resource_refs=(),
    )
    assert req.operation == "analyze_risk"

    # Attacker tries to spoof account_id
    with pytest.raises(ValidationError):
        AgentRunRequestV1(
            operation="analyze_risk",
            surface="pro_lab",
            account_id="victim_account",  # type: ignore
        )

    # Attacker tries to escalate scopes
    with pytest.raises(ValidationError):
        AgentRunRequestV1(
            operation="analyze_risk",
            surface="pro_lab",
            scopes=("admin:all",),  # type: ignore
        )

    # Attacker tries to inject allowed_capabilities
    with pytest.raises(ValidationError):
        AgentRunRequestV1(
            operation="analyze_risk",
            surface="pro_lab",
            allowed_capabilities=("quant:all",),  # type: ignore
        )


def test_models_are_frozen_immutable() -> None:
    """Iron Rule 4: ConfigDict(frozen=True)."""
    artifact = AgentArtifact(
        artifact_id="artifact-1",
        artifact_type="analysis",
        domain="finance",
        account_id="account-a",
        authoring_run_id="run-1",
        created_at=NOW,
    )
    with pytest.raises(ValidationError):
        artifact.review_status = "accepted"  # type: ignore


def test_ten_canonical_domain_artifacts_round_trip() -> None:
    from risk_dashboard.modules.agentic_core.schemas import (
        NextBestActionCardV1,
        FormulaWalkthrough,
        SocraticHint,
        CheckpointReview,
        LineItemExplanation,
        EarningsQualityMemo,
        PreflightChecklist,
        BacktestCritiqueArtifact,
        NewsEvidenceBrief,
        PortfolioReviewArtifactV1,
    )

    models = [
        NextBestActionCardV1(
            task_title="Thực hành độ biến động",
            evidence_rationale="Hoàn thành bài Tỷ suất sinh lời",
            deeplink="/simulation/volatility",
        ),
        FormulaWalkthrough(
            formula_latex=r"VaR_{\alpha} = -\inf \{ l \in \mathbb{R} : P(L > l) \le 1 - \alpha \}",
            economic_intuition="Tổn thất tối đa tại mức tin cậy",
        ),
        SocraticHint(
            hint_level=1,
            guiding_question="Doanh thu tăng nhưng dòng tiền CFO âm có bình thường không?",
            cause_effect_clue="Xem xét khoản phải thu khách hàng",
        ),
        CheckpointReview(
            checkpoint_id="chk_01",
            mastered_concepts=("Tỷ suất lợi nhuận ròng", "Vòng quay tài sản"),
            misconceptions=("Nhầm lẫn giữa lợi nhuận kế toán và dòng tiền",),
            recommended_action="Đọc lại bài Báo cáo lưu chuyển tiền tệ",
        ),
        LineItemExplanation(
            line_item_code="CFO",
            definition="Dòng tiền thuần từ hoạt động kinh doanh",
            calculation_formula="EBIT + Khấu hao - Thuế - Thay đổi Vốn lưu động",
        ),
        EarningsQualityMemo(
            ticker="VNM",
            period="2026Q2",
            cfo_to_net_income_ratio=1.15,
            accruals_metric=0.04,
            red_flags=(),
            conclusion_summary="Chất lượng lợi nhuận cao, được bảo chứng bởi dòng tiền thực.",
        ),
        PreflightChecklist(
            strategy_id="strat_mean_reversion",
            statistical_assumption_checks=("Chuỗi giá dừng sau lấy sai phân bậc 1",),
            data_sufficiency=True,
            lookahead_bias_detected=False,
            overfitting_risk_rating="low",
        ),
        BacktestCritiqueArtifact(
            backtest_id="bt_101",
            max_drawdown_pct=-14.2,
            sharpe_ratio_net_fees=1.85,
            slippage_assumptions={"model": "linear", "basis_points": 5},
            critique_notes=("Chiến lược kiểm soát drawdown tốt.",),
        ),
        NewsEvidenceBrief(
            cluster_id="cluster_rates_sbv",
            verified_facts=("NHNN giảm lãi suất điều hành 0.25%",),
            party_claims=("Doanh nghiệp kỳ vọng chi phí vốn giảm",),
            hypotheses=("Biên lãi ròng NIM ngân hàng có thể co hẹp",),
            importance_score=0.92,
        ),
        PortfolioReviewArtifactV1(
            portfolio_id="port_paper_alpha",
            cash_allocation_pct=25.0,
            equity_allocation_pct=75.0,
            portfolio_beta=1.05,
            shock_scenarios={"vn_index_drop_10pct": -10.5},
            concentration_warnings=("Tỷ trọng ngành ngân hàng đạt 30%",),
        ),
    ]

    for model in models:
        json_data = model.model_dump_json()
        restored = type(model).model_validate_json(json_data)
        assert restored == model
        assert restored.schema_version == "1.0.0"

        # Verify frozen
        with pytest.raises(ValidationError):
            setattr(model, "schema_version", "2.0.0")  # type: ignore

        # Verify extra="forbid"
        raw_dict = model.model_dump()
        raw_dict["unauthorized_injected_key"] = "exploit"
        with pytest.raises(ValidationError):
            type(model).model_validate(raw_dict)


def test_agentic_requests_must_have_schema_version() -> None:
    """BUG-16: AgentRunRequestV1 và AgentRunResponseV1 phải có schema_version == '1.0.0' theo ADR-002."""
    req = AgentRunRequestV1(
        operation="analyze_risk",
        surface="pro_lab",
    )
    res = AgentRunResponseV1(
        run_id="run-test-1",
        status="succeeded",
    )

    assert hasattr(req, "schema_version"), "AgentRunRequestV1 thiếu trường schema_version"
    assert req.schema_version == "1.0.0"

    assert hasattr(res, "schema_version"), "AgentRunResponseV1 thiếu trường schema_version"
    assert res.schema_version == "1.0.0"

    # Đồng thời xác minh round-trip serialize/deserialize
    req_json = req.model_dump_json()
    assert AgentRunRequestV1.model_validate_json(req_json) == req

    res_json = res.model_dump_json()
    assert AgentRunResponseV1.model_validate_json(res_json) == res


