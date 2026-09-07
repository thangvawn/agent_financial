"""Orchestration service for quant_research operations."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import uuid
from typing import Any

from risk_dashboard.modules.auth.domain.policies import has_scope
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.quant_research.application.reviewer import QuantNumericReviewer
from risk_dashboard.modules.quant_research.domain.ports import QuantEnginePort
from risk_dashboard.modules.quant_research.infrastructure.engine_adapter import (
    QuantAdapterError,
    QuantEngineAdapter,
)
from risk_dashboard.modules.quant_research.schemas.artifacts import QuantResearchArtifactV1
from risk_dashboard.modules.quant_research.schemas.requests import QuantResearchRequestV1
from risk_dashboard.modules.quant_research.schemas.tools import QuantToolResultV1
from risk_dashboard.platform.ai_runtime.contracts import (
    ModelMessage,
    ModelSettings,
    ModelTask,
)
from risk_dashboard.platform.ai_runtime.factory import get_default_provider
from risk_dashboard.platform.ai_runtime.provider import LLMProvider

logger = logging.getLogger(__name__)

OPERATION_SCOPE_MAP = {
    "eod_analysis": "quant_research:analysis:read",
    "scenario_compare": "quant_research:scenario:read",
    "model_report": "quant_research:model_report:read",
}


class QuantResearchService:
    """Orchestrates quantitative research queries with exact reviewer verification."""

    def __init__(
        self,
        *,
        engine_adapter: QuantEnginePort | None = None,
        reviewer: QuantNumericReviewer | None = None,
        provider: LLMProvider | None = None,
    ) -> None:
        self._adapter = engine_adapter or QuantEngineAdapter()
        self._reviewer = reviewer or QuantNumericReviewer()
        self._provider = provider

    def _get_provider(self) -> LLMProvider:
        if self._provider is not None:
            return self._provider
        return get_default_provider()

    async def execute_research(
        self,
        *,
        request: QuantResearchRequestV1,
        principal: AuthPrincipal,
    ) -> QuantResearchArtifactV1:
        """Execute quant research workflow: authorize -> run engine -> synthesize -> review."""
        # 1. Authorize principal scope
        required_scope = OPERATION_SCOPE_MAP.get(request.operation)
        if required_scope and not has_scope(principal, required_scope):
            raise QuantAdapterError(
                "invalid_input",
                f"Principal '{principal.account_id}' lacks required scope '{required_scope}' "
                f"for operation '{request.operation}'.",
                hint="Kiểm tra lại quyền truy cập quant_research của tài khoản.",
            )

        run_id = request.run_id or f"qr-{uuid.uuid4().hex[:12]}"

        # 2. Dispatch to engine adapter
        if request.operation == "eod_analysis":
            assert request.as_of is not None
            tool_result = await self._adapter.run_eod_analysis(as_of=request.as_of, run_id=run_id)
        elif request.operation == "scenario_compare":
            assert request.as_of is not None
            tool_result = await self._adapter.compare_macro_scenario(
                as_of=request.as_of,
                usd_vnd_rate=request.usd_vnd_rate,
                sbv_interest_rate_pct=request.sbv_interest_rate_pct,
            )
        elif request.operation == "model_report":
            tool_result = await self._adapter.get_model_research_report(model_ref="latest")
        else:
            raise QuantAdapterError("invalid_input", f"Unsupported operation '{request.operation}'.")

        # 3. Synthesize explanation using AI Runtime or deterministic fallback
        candidate = await self._synthesize_candidate(request, tool_result, run_id)

        # 4. Deterministic Reviewer Gate
        verified_artifact = self._reviewer.review(candidate=candidate, tool_result=tool_result)
        return verified_artifact

    async def _synthesize_candidate(
        self,
        request: QuantResearchRequestV1,
        tool_result: QuantToolResultV1,
        run_id: str,
    ) -> QuantResearchArtifactV1:
        now = datetime.now(timezone.utc)
        payload = tool_result.payload

        # Attempt structured narrative generation via provider
        try:
            provider = self._get_provider()
            task = ModelTask(
                task_type="quant_research_narrative",
                system_instructions_ref="quant_research_system_v1",
                messages=(
                    ModelMessage(
                        role="system",
                        content=(
                            "You are a Quantitative Finance Research Assistant. "
                            "Explain the quantitative findings strictly using the numbers provided in the payload. "
                            "DO NOT invent numbers. DO NOT offer investment advice. DO NOT mention quantum computing. "
                            "Output must be a valid JSON object matching the requested schema."
                        ),
                    ),
                    ModelMessage(
                        role="user",
                        content=json.dumps(
                            {
                                "question": request.question,
                                "operation": request.operation,
                                "payload": payload,
                            },
                            default=str,
                        ),
                    ),
                ),
                settings=ModelSettings(temperature=0.2, response_format="json_object"),
                correlation_id=run_id,
                deadline_seconds=15.0,
            )
            result = await provider.generate(task)
            parsed: dict[str, Any] | None = result.parsed
            if not parsed and result.text:
                try:
                    parsed = json.loads(result.text)
                except Exception:
                    parsed = None

            if parsed and isinstance(parsed, dict):
                return QuantResearchArtifactV1(
                    schema_version="1.0.0",
                    artifact_type="quant_research",
                    run_id=run_id,
                    operation=request.operation,
                    headline=str(parsed.get("headline", "Kết quả phân tích định lượng")),
                    findings=tuple(parsed.get("findings", ())),
                    metrics=dict(parsed.get("metrics", {})),
                    source_refs=tool_result.source_refs,
                    assumptions=tuple(parsed.get("assumptions", ())),
                    limitations=tuple(parsed.get("limitations", ("Mô hình định lượng tham khảo",))),
                    review_status="verified",
                    generated_at=now,
                )
        except Exception as exc:
            logger.warning("AI Runtime narrative generation fallback: %s", exc)

        # Deterministic safe fallback directly from payload
        return self._build_deterministic_candidate(request, tool_result, run_id, now)

    def _build_deterministic_candidate(
        self,
        request: QuantResearchRequestV1,
        tool_result: QuantToolResultV1,
        run_id: str,
        now: datetime,
    ) -> QuantResearchArtifactV1:
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

