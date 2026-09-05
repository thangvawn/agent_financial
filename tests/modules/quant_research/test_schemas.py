"""Tests for quant_research schemas (QF0 Exit Gate)."""
from __future__ import annotations

from datetime import date, datetime, timezone
import pytest
from pydantic import ValidationError

from risk_dashboard.modules.quant_research.schemas.artifacts import QuantResearchArtifactV1
from risk_dashboard.modules.quant_research.schemas.requests import QuantResearchRequestV1
from risk_dashboard.modules.quant_research.schemas.tools import (
    QuantSourceRefV1,
    QuantToolResultV1,
)


def test_eod_request_valid_roundtrip() -> None:
    req = QuantResearchRequestV1(
        operation="eod_analysis",
        question="Phân tích rủi ro thị trường ngày 2026-03-30",
        as_of=date(2026, 3, 30),
        run_id="run-123",
    )
    raw = req.model_dump(mode="json")
    restored = QuantResearchRequestV1.model_validate(raw)
    assert restored == req
    assert restored.schema_version == "1.0.0"
    assert restored.operation == "eod_analysis"
    assert restored.as_of == date(2026, 3, 30)


def test_scenario_request_valid_roundtrip() -> None:
    req = QuantResearchRequestV1(
        operation="scenario_compare",
        question="Mô phỏng kịch bản tỷ giá tăng",
        as_of=date(2026, 3, 30),
        usd_vnd_rate=26000.0,
        sbv_interest_rate_pct=5.5,
    )
    raw = req.model_dump(mode="json")
    restored = QuantResearchRequestV1.model_validate(raw)
    assert restored == req
    assert restored.usd_vnd_rate == 26000.0
    assert restored.sbv_interest_rate_pct == 5.5


def test_model_report_request_valid_roundtrip() -> None:
    req = QuantResearchRequestV1(
        operation="model_report",
        question="Báo cáo benchmark mô hình mới nhất",
    )
    raw = req.model_dump(mode="json")
    restored = QuantResearchRequestV1.model_validate(raw)
    assert restored == req
    assert restored.as_of is None
    assert restored.usd_vnd_rate is None
    assert restored.sbv_interest_rate_pct is None


def test_request_extra_forbid_rejects_authority_and_injection_fields() -> None:
    forbidden_payloads = [
        {"account_id": "acc-hacker"},
        {"scopes": ["admin:all"]},
        {"tool_name": "quant.eod_analysis.v1"},
        {"model_dir": "/etc/passwd"},
        {"path": "../../secret.env"},
        {"is_admin": True},
    ]
    for extra in forbidden_payloads:
        with pytest.raises(ValidationError) as exc_info:
            QuantResearchRequestV1(
                operation="eod_analysis",
                question="Kiểm tra bảo mật",
                as_of=date(2026, 3, 30),
                **extra,  # type: ignore[arg-type]
            )
        assert "Extra inputs are not permitted" in str(exc_info.value)


def test_eod_requires_as_of() -> None:
    with pytest.raises(ValidationError) as exc_info:
        QuantResearchRequestV1(
            operation="eod_analysis",
            question="Thiếu ngày as_of",
            as_of=None,
        )
    assert "requires 'as_of' date" in str(exc_info.value)


def test_scenario_requires_as_of() -> None:
    with pytest.raises(ValidationError) as exc_info:
        QuantResearchRequestV1(
            operation="scenario_compare",
            question="Thiếu as_of",
            as_of=None,
            usd_vnd_rate=25500.0,
        )
    assert "requires 'as_of' date" in str(exc_info.value)


def test_scenario_requires_at_least_one_override() -> None:
    with pytest.raises(ValidationError) as exc_info:
        QuantResearchRequestV1(
            operation="scenario_compare",
            question="Thiếu cả 2 overrides",
            as_of=date(2026, 3, 30),
            usd_vnd_rate=None,
            sbv_interest_rate_pct=None,
        )
    assert "requires at least one macro override" in str(exc_info.value)


def test_scenario_allows_single_or_both_overrides() -> None:
    # Only usd_vnd_rate
    r1 = QuantResearchRequestV1(
        operation="scenario_compare",
        question="Chỉ USD/VND",
        as_of=date(2026, 3, 30),
        usd_vnd_rate=25000.0,
    )
    assert r1.usd_vnd_rate == 25000.0
    assert r1.sbv_interest_rate_pct is None

    # Only sbv_interest_rate_pct
    r2 = QuantResearchRequestV1(
        operation="scenario_compare",
        question="Chỉ SBV",
        as_of=date(2026, 3, 30),
        sbv_interest_rate_pct=6.0,
    )
    assert r2.sbv_interest_rate_pct == 6.0
    assert r2.usd_vnd_rate is None


def test_model_report_rejects_macro_overrides() -> None:
    with pytest.raises(ValidationError) as exc_info:
        QuantResearchRequestV1(
            operation="model_report",
            question="Model report có override",
            usd_vnd_rate=25000.0,
        )
    assert "does not accept macro overrides" in str(exc_info.value)


def test_question_bounds() -> None:
    with pytest.raises(ValidationError):
        QuantResearchRequestV1(
            operation="model_report",
            question="",  # Empty
        )

    with pytest.raises(ValidationError):
        QuantResearchRequestV1(
            operation="model_report",
            question="x" * 4001,  # Exceeds max 4000
        )


def test_rate_bounds() -> None:
    # usd_vnd_rate <= 0
    with pytest.raises(ValidationError):
        QuantResearchRequestV1(
            operation="scenario_compare",
            question="Tỷ giá âm",
            as_of=date(2026, 3, 30),
            usd_vnd_rate=0.0,
        )

    # usd_vnd_rate > 1_000_000
    with pytest.raises(ValidationError):
        QuantResearchRequestV1(
            operation="scenario_compare",
            question="Tỷ giá quá lớn",
            as_of=date(2026, 3, 30),
            usd_vnd_rate=1_000_001.0,
        )

    # sbv_interest_rate_pct < -10
    with pytest.raises(ValidationError):
        QuantResearchRequestV1(
            operation="scenario_compare",
            question="Lãi suất âm quá mức",
            as_of=date(2026, 3, 30),
            sbv_interest_rate_pct=-11.0,
        )

    # sbv_interest_rate_pct > 100
    with pytest.raises(ValidationError):
        QuantResearchRequestV1(
            operation="scenario_compare",
            question="Lãi suất quá 100%",
            as_of=date(2026, 3, 30),
            sbv_interest_rate_pct=105.0,
        )


def test_tool_result_and_source_ref_roundtrip() -> None:
    now = datetime.now(timezone.utc)
    source_ref = QuantSourceRefV1(
        source_id="panel_eod_vnindex",
        source_type="panel",
        version="panel_20260330",
        as_of=now,
    )
    result = QuantToolResultV1(
        tool_name="quant.eod_analysis.v1",
        status="ok",
        payload={"decision_score": 0.72, "regime": "risk_off"},
        source_refs=(source_ref,),
        warnings=("High volatility period",),
        generated_at=now,
    )
    dumped = result.model_dump(mode="json")
    restored = QuantToolResultV1.model_validate(dumped)
    assert restored.tool_name == "quant.eod_analysis.v1"
    assert restored.status == "ok"
    assert restored.payload["decision_score"] == 0.72
    assert len(restored.source_refs) == 1
    assert restored.source_refs[0].source_id == "panel_eod_vnindex"

    # Extra fields rejected
    with pytest.raises(ValidationError):
        QuantToolResultV1(
            tool_name="quant.eod_analysis.v1",
            status="ok",
            payload={},
            source_refs=(),
            generated_at=now,
            extra_bad_field="hack",  # type: ignore[call-arg]
        )


def test_artifact_schema_roundtrip() -> None:
    now = datetime.now(timezone.utc)
    source_ref = QuantSourceRefV1(
        source_id="model_risk_xgb",
        source_type="model",
        version="skhgb-v4-hybrid",
        as_of=now,
    )
    artifact = QuantResearchArtifactV1(
        run_id="run-quant-001",
        operation="eod_analysis",
        headline="Thị trường nghiêng về trạng thái rủi ro ngắn hạn",
        findings=(
            "Điểm quyết định đạt 0.72, vượt ngưỡng cảnh báo 0.65",
            "Yếu tố chi phối chính là tỷ giá USD/VND biến động mạnh",
        ),
        metrics={"decision_score": 0.72, "regime": "risk_off", "p1w": 0.68},
        source_refs=(source_ref,),
        assumptions=("Dữ liệu giá đóng cửa ngày 2026-03-30 đã hoàn tất",),
        limitations=(
            "Mô hình thống kê định lượng, không phải khuyến nghị đầu tư",
            "Độ chính xác phụ thuộc tính toàn vẹn của panel dữ liệu",
        ),
        review_status="verified",
        generated_at=now,
    )
    dumped = artifact.model_dump(mode="json")
    restored = QuantResearchArtifactV1.model_validate(dumped)
    assert restored.run_id == "run-quant-001"
    assert restored.review_status == "verified"
    assert restored.metrics["decision_score"] == 0.72
    assert len(restored.limitations) == 2

    # Extra fields rejected
    with pytest.raises(ValidationError):
        QuantResearchArtifactV1(
            run_id="run-quant-001",
            operation="eod_analysis",
            headline="Test",
            findings=(),
            metrics={},
            source_refs=(),
            limitations=("None",),
            review_status="verified",
            generated_at=now,
            unauthorized_secret="secret",  # type: ignore[call-arg]
        )


def test_json_schema_snapshot() -> None:
    """Snapshot asserting core JSON schema definitions exist and enforce extra=forbid."""
    req_schema = QuantResearchRequestV1.model_json_schema()
    assert req_schema["additionalProperties"] is False
    assert "operation" in req_schema["properties"]
    assert "question" in req_schema["properties"]

    tool_schema = QuantToolResultV1.model_json_schema()
    assert tool_schema["additionalProperties"] is False
    assert "payload" in tool_schema["properties"]

    artifact_schema = QuantResearchArtifactV1.model_json_schema()
    assert artifact_schema["additionalProperties"] is False
    assert "review_status" in artifact_schema["properties"]

