"""Tests for QuantResearchService & QuantNumericReviewer (QF2 Exit Gate & Mutation Backtest)."""
from __future__ import annotations

from datetime import date, datetime, timezone
import pytest

from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.quant_research.application.reviewer import QuantNumericReviewer
from risk_dashboard.modules.quant_research.application.service import QuantResearchService
from risk_dashboard.modules.quant_research.infrastructure.engine_adapter import (
    QuantAdapterError,
    QuantEngineAdapter,
)
from risk_dashboard.modules.quant_research.schemas.artifacts import QuantResearchArtifactV1
from risk_dashboard.modules.quant_research.schemas.requests import QuantResearchRequestV1
from risk_dashboard.modules.quant_research.schemas.tools import (
    QuantSourceRefV1,
    QuantToolResultV1,
)
from risk_dashboard.platform.ai_runtime.contracts import ModelResult, TokenUsage
from risk_dashboard.platform.ai_runtime.testing.fake_provider import FakeProvider
from risk_dashboard.platform.runtime.panel_store import set_panel_for_testing


@pytest.fixture(autouse=True)
def setup_panel(synthetic_panel):
    set_panel_for_testing(synthetic_panel)
    return synthetic_panel


def _principal(scopes: tuple[str, ...] = ("quant_research:analysis:read",)) -> AuthPrincipal:
    return AuthPrincipal(
        account_id="acc-quant-01",
        session_id="sess-quant-01",
        scopes=scopes,
        resolved_at="2026-09-05T12:00:00+00:00",
    )


def _sample_tool_result() -> QuantToolResultV1:
    now = datetime.now(timezone.utc)
    return QuantToolResultV1(
        tool_name="quant.eod_analysis.v1",
        status="ok",
        payload={
            "decision_score": 0.6543,
            "risk_regime": "high",
            "horizons": {
                "p_decline_1w": 0.612,
                "p_decline_2w": 0.685,
                "p_decline_1m": 0.722,
                "expected_drawdown_pct": -4.5,
            },
            "dominant_feature": "usd_vnd_1m_change_pct",
        },
        source_refs=(
            QuantSourceRefV1(
                source_id="panel_test",
                source_type="panel",
                version="v1",
                as_of=now,
            ),
        ),
        generated_at=now,
    )


def _valid_candidate(tool_result: QuantToolResultV1) -> QuantResearchArtifactV1:
    return QuantResearchArtifactV1(
        run_id="run-rev-01",
        operation="eod_analysis",
        headline="Đánh giá rủi ro thị trường",
        findings=("Điểm rủi ro đạt 0.6543, trạng thái rủi ro cao.",),
        metrics={
            "decision_score": 0.6543,
            "risk_regime": "high",
            "p_decline_1w": 0.612,
        },
        source_refs=tool_result.source_refs,
        assumptions=("Dữ liệu panel hợp lệ",),
        limitations=("Mô hình thống kê định lượng, không phải khuyến nghị đầu tư",),
        review_status="verified",
        generated_at=tool_result.generated_at,
    )


# ---------------------------------------------------------------------------
# Reviewer Mutation Backtest (100% block rate)
# ---------------------------------------------------------------------------


def test_reviewer_passes_valid_artifact() -> None:
    reviewer = QuantNumericReviewer()
    tool_result = _sample_tool_result()
    candidate = _valid_candidate(tool_result)

    reviewed = reviewer.review(candidate=candidate, tool_result=tool_result)
    assert reviewed.review_status == "verified"


def test_reviewer_blocks_altered_decision_score() -> None:
    reviewer = QuantNumericReviewer()
    tool_result = _sample_tool_result()
    candidate = _valid_candidate(tool_result)

    # Injected mismatch: change 0.6543 -> 0.9999
    mutated = candidate.model_copy(
        update={"metrics": {**candidate.metrics, "decision_score": 0.9999}}
    )
    reviewed = reviewer.review(candidate=mutated, tool_result=tool_result)
    assert reviewed.review_status == "blocked"
    assert any("Numeric mismatch for 'decision_score'" in lim for lim in reviewed.limitations)


def test_reviewer_blocks_altered_horizon_probability() -> None:
    reviewer = QuantNumericReviewer()
    tool_result = _sample_tool_result()
    candidate = _valid_candidate(tool_result)

    # Injected mismatch: change p_decline_1w from 0.612 -> 0.100
    mutated = candidate.model_copy(
        update={"metrics": {**candidate.metrics, "p_decline_1w": 0.100}}
    )
    reviewed = reviewer.review(candidate=mutated, tool_result=tool_result)
    assert reviewed.review_status == "blocked"
    assert any("Numeric mismatch for 'p_decline_1w'" in lim for lim in reviewed.limitations)


def test_reviewer_blocks_nan_or_inf() -> None:
    reviewer = QuantNumericReviewer()
    tool_result = _sample_tool_result()
    candidate = _valid_candidate(tool_result)

    # Inject float('nan')
    mutated_nan = candidate.model_copy(
        update={"metrics": {**candidate.metrics, "decision_score": float("nan")}}
    )
    assert reviewer.review(candidate=mutated_nan, tool_result=tool_result).review_status == "blocked"

    # Inject float('inf')
    mutated_inf = candidate.model_copy(
        update={"metrics": {**candidate.metrics, "decision_score": float("inf")}}
    )
    assert reviewer.review(candidate=mutated_inf, tool_result=tool_result).review_status == "blocked"


def test_reviewer_blocks_empty_source_refs() -> None:
    reviewer = QuantNumericReviewer()
    tool_result = _sample_tool_result()
    candidate = _valid_candidate(tool_result).model_copy(update={"source_refs": ()})

    reviewed = reviewer.review(candidate=candidate, tool_result=tool_result)
    assert reviewed.review_status == "blocked"
    assert any("missing required source_refs" in lim for lim in reviewed.limitations)


def test_reviewer_blocks_empty_limitations() -> None:
    reviewer = QuantNumericReviewer()
    tool_result = _sample_tool_result()
    candidate = _valid_candidate(tool_result).model_copy(update={"limitations": ()})

    reviewed = reviewer.review(candidate=candidate, tool_result=tool_result)
    assert reviewed.review_status == "blocked"
    assert any("missing required limitations" in lim for lim in reviewed.limitations)


def test_reviewer_blocks_forbidden_investment_advice() -> None:
    reviewer = QuantNumericReviewer()
    tool_result = _sample_tool_result()
    candidate = _valid_candidate(tool_result).model_copy(
        update={"headline": "Khuyến nghị mua cổ phiếu ngay hôm nay"}
    )

    reviewed = reviewer.review(candidate=candidate, tool_result=tool_result)
    assert reviewed.review_status == "blocked"
    assert any("investment advice" in lim for lim in reviewed.limitations)


def test_reviewer_blocks_forbidden_quantum_computing_claims() -> None:
    reviewer = QuantNumericReviewer()
    tool_result = _sample_tool_result()
    candidate = _valid_candidate(tool_result).model_copy(
        update={"findings": ("Sử dụng mạch lượng tử QAOA trên 50 qubits",)}
    )

    reviewed = reviewer.review(candidate=candidate, tool_result=tool_result)
    assert reviewed.review_status == "blocked"
    assert any("quantum computing" in lim for lim in reviewed.limitations)


# ---------------------------------------------------------------------------
# Service E2E & FakeProvider Tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_service_e2e_with_fake_provider(as_of_date) -> None:
    fake_provider = FakeProvider(
        scripted=[
            ModelResult(
                parsed={
                    "headline": "Báo cáo rủi ro thị trường từ AI Provider",
                    "findings": ["Rủi ro được ghi nhận ở mức trung tính/cao."],
                    "metrics": {"decision_score": 0.5},
                    "assumptions": ["Dữ liệu đầy đủ"],
                    "limitations": ["Mô hình tham khảo, không khuyến nghị"],
                },
                text="",
                provider="fake",
                model="fake-model",
                latency_ms=10,
                finish_reason="stop",
                usage=TokenUsage(prompt=10, completion=10, total=20),
            )
        ]
    )

    service = QuantResearchService(
        engine_adapter=QuantEngineAdapter(),
        reviewer=QuantNumericReviewer(),
        provider=fake_provider,
    )

    req = QuantResearchRequestV1(
        operation="eod_analysis",
        question="Phân tích tình hình rủi ro hiện tại",
        as_of=as_of_date,
    )
    principal = _principal(("quant_research:analysis:read",))

    artifact = await service.execute_research(request=req, principal=principal)
    assert artifact.operation == "eod_analysis"
    assert len(artifact.source_refs) > 0
    assert len(artifact.limitations) > 0


@pytest.mark.anyio
async def test_service_deterministic_fallback(as_of_date) -> None:
    # Service without provider defaults to deterministic fallback directly from payload
    service = QuantResearchService(
        engine_adapter=QuantEngineAdapter(),
        reviewer=QuantNumericReviewer(),
        provider=FakeProvider(scripted=[]),  # will raise provider_unavailable -> triggers fallback
    )

    req = QuantResearchRequestV1(
        operation="eod_analysis",
        question="Chạy phân tích EOD không cần LLM",
        as_of=as_of_date,
    )
    principal = _principal(("quant_research:analysis:read",))

    artifact = await service.execute_research(request=req, principal=principal)
    assert artifact.review_status == "verified"
    assert "Báo cáo rủi ro thị trường EOD" in artifact.headline
    assert "decision_score" in artifact.metrics
    assert len(artifact.limitations) > 0


@pytest.mark.anyio
async def test_service_denies_missing_scope(as_of_date) -> None:
    service = QuantResearchService()
    req = QuantResearchRequestV1(
        operation="eod_analysis",
        question="Thiếu quyền",
        as_of=as_of_date,
    )
    # Principal only has scenario scope, not analysis scope
    unauthorized_principal = _principal(("quant_research:scenario:read",))

    with pytest.raises(QuantAdapterError) as exc_info:
        await service.execute_research(request=req, principal=unauthorized_principal)
    assert exc_info.value.error_type == "invalid_input"
    assert "lacks required scope" in exc_info.value.message


def test_build_candidate_from_llm_explicit_normalization() -> None:
    from datetime import datetime, timezone
    from risk_dashboard.modules.quant_research.application.candidate_builder import build_candidate_from_llm

    tool_result = _sample_tool_result()
    req = QuantResearchRequestV1(
        operation="eod_analysis",
        question="Test normalization",
        as_of=date(2015, 12, 30),
    )
    now = datetime.now(timezone.utc)

    parsed = {
        "headline": "Tiêu đề kiểm tra",
        "findings": ["Phát hiện 1", "Phát hiện 2"],
        "metrics": {"decision_score": 0.6543},
        "assumptions": ["Giả định 1"],
        "limitations": ["Giới hạn 1"],
    }
    cand = build_candidate_from_llm(parsed, req, tool_result, "run-1", now)
    assert isinstance(cand.findings, tuple)
    assert cand.findings == ("Phát hiện 1", "Phát hiện 2")
    assert isinstance(cand.metrics, dict)
    assert cand.metrics == {"decision_score": 0.6543}

    # Test with sparse / None fields
    parsed_sparse = {"metrics": None}
    cand_sparse = build_candidate_from_llm(parsed_sparse, req, tool_result, "run-2", now)
    assert cand_sparse.findings == ()
    assert cand_sparse.metrics == {}
    assert cand_sparse.assumptions == ()
    assert cand_sparse.limitations == ("Mô hình định lượng tham khảo",)

