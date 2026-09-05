"""Artifact candidate builder for quant research service."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from risk_dashboard.modules.quant_research.schemas.artifacts import QuantResearchArtifactV1
from risk_dashboard.modules.quant_research.schemas.requests import QuantResearchRequestV1
from risk_dashboard.modules.quant_research.schemas.tools import QuantToolResultV1


def build_candidate_from_llm(
    parsed: dict[str, Any],
    request: QuantResearchRequestV1,
    tool_result: QuantToolResultV1,
    run_id: str,
    now: datetime,
) -> QuantResearchArtifactV1:
    """Build artifact candidate from LLM parsed response."""
    raw_findings = parsed.get("findings")
    findings = tuple(str(x) for x in raw_findings) if isinstance(raw_findings, (list, tuple)) else ()

    raw_metrics = parsed.get("metrics")
    metrics = dict(raw_metrics) if isinstance(raw_metrics, dict) else {}

    raw_assumptions = parsed.get("assumptions")
    assumptions = tuple(str(x) for x in raw_assumptions) if isinstance(raw_assumptions, (list, tuple)) else ()

    raw_limitations = parsed.get("limitations")
    limitations = (
        tuple(str(x) for x in raw_limitations)
        if isinstance(raw_limitations, (list, tuple)) and raw_limitations
        else ("Mô hình định lượng tham khảo",)
    )

    return QuantResearchArtifactV1(
        schema_version="1.0.0",
        artifact_type="quant_research",
        run_id=run_id,
        operation=request.operation,
        headline=str(parsed.get("headline") or "Kết quả phân tích định lượng"),
        findings=findings,
        metrics=metrics,
        source_refs=tool_result.source_refs,
        assumptions=assumptions,
        limitations=limitations,
        review_status="verified",
        generated_at=now,
    )


def build_deterministic_candidate(
    request: QuantResearchRequestV1,
    tool_result: QuantToolResultV1,
    run_id: str,
    now: datetime,
) -> QuantResearchArtifactV1:
    """Build deterministic, verifiable candidate directly from tool payload."""
    payload = tool_result.payload
    if request.operation == "eod_analysis":
        score = payload.get("decision_score")
        regime = payload.get("risk_regime", "neutral")
        metrics = {
            "decision_score": score,
            "risk_regime": regime,
        }
        if "horizons" in payload:
            horizons = payload["horizons"]
            metrics["p_decline_1w"] = horizons.get("p_decline_1w")
            metrics["p_decline_2w"] = horizons.get("p_decline_2w")
            metrics["p_decline_1m"] = horizons.get("p_decline_1m")

        findings = (
            f"Điểm quyết định rủi ro thị trường đạt {score}, trạng thái ghi nhận: {regime}.",
            f"Yếu tố chi phối chính trong kỳ phân tích: {payload.get('dominant_feature', 'n/a')}.",
        )
        headline = f"Báo cáo rủi ro thị trường EOD ngày {request.as_of}"
    elif request.operation == "scenario_compare":
        score = payload.get("decision_score")
        regime = payload.get("risk_regime", "neutral")
        metrics = {
            "decision_score": score,
            "risk_regime": regime,
        }
        findings = (
            f"Kịch bản vĩ mô giả định điều chỉnh tỷ giá/lãi suất: điểm rủi ro dự kiến {score}.",
            f"Trạng thái thị trường ứng với kịch bản: {regime}.",
        )
        headline = f"Phân tích kịch bản sốc vĩ mô ngày {request.as_of}"
    else:
        summary = payload.get("summary", {})
        metrics = {
            "model_version": summary.get("model_version"),
        }
        findings = (
            f"Phiên bản mô hình benchmark hiện hành: {summary.get('model_version')}.",
            f"Thời điểm huấn luyện gần nhất: {summary.get('train_as_of')}.",
        )
        headline = "Báo cáo năng lực và kiểm định mô hình định lượng"

    return QuantResearchArtifactV1(
        schema_version="1.0.0",
        artifact_type="quant_research",
        run_id=run_id,
        operation=request.operation,
        headline=headline,
        findings=findings,
        metrics=metrics,
        source_refs=tool_result.source_refs,
        assumptions=("Dữ liệu đầu vào phản ánh snapshot thị trường đã chốt sổ",),
        limitations=(
            "Mô hình nghiên cứu định lượng thuần túy, không cấu thành khuyến nghị đầu tư.",
            "Kết quả phụ thuộc vào tính toàn vẹn của dữ liệu vĩ mô và panel lịch sử.",
        ),
        review_status="verified",
        generated_at=now,
    )
