"""Orchestration service for quant_research operations."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import uuid
from typing import Any

from risk_dashboard.modules.auth.domain.policies import has_scope
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.quant_research.application.candidate_builder import (
    build_candidate_from_llm,
    build_deterministic_candidate,
)
from risk_dashboard.modules.quant_research.application.reviewer import QuantNumericReviewer
from risk_dashboard.modules.quant_research.domain.errors import QuantAdapterError
from risk_dashboard.modules.quant_research.domain.ports import QuantEnginePort
from risk_dashboard.modules.quant_research.infrastructure.engine_adapter import QuantEngineAdapter
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
                return build_candidate_from_llm(parsed, request, tool_result, run_id, now)
        except Exception as exc:
            logger.warning("AI Runtime narrative generation fallback: %s", exc)

        return build_deterministic_candidate(request, tool_result, run_id, now)
