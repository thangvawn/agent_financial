"""AI-backed endpoints for Pro Lab using Shared AI Runtime (platform.ai_runtime).

Turns natural-language ideas into structured strategy blueprints, swarm reviews,
and backtest analyses via LLMProvider protocol.
"""
from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse

from risk_dashboard.modules.pro_lab.api.ai_helpers import (
    get_ai_provider,
    get_ai_provider_or_none,
    require_pro_scope,
)
from risk_dashboard.modules.pro_lab.api.ai_prompts import STRATEGY_SYSTEM_PROMPT
from risk_dashboard.modules.pro_lab.application.ai_service import (
    execute_backtest_critique,
    execute_strategy_copilot,
    execute_swarm_committee,
)
from risk_dashboard.modules.pro_lab.schemas.ai import (
    AIHealthResponse,
    BacktestCritiqueRequest,
    BacktestCritiqueResponse,
    StrategyCopilotRequest,
    StrategyCopilotResponse,
    SwarmCommitteeRequest,
    SwarmCommitteeResponse,
)
from risk_dashboard.platform.ai_runtime.contracts import (
    ModelError,
    ModelMessage,
    ModelSettings,
    ModelTask,
    StreamEvent,
)
from risk_dashboard.platform.ai_runtime.provider import LLMProvider
from risk_dashboard.platform.ai_runtime.sse import format_sse_event
from risk_dashboard.platform.ai_runtime.streaming import with_stream_deadline
from risk_dashboard.platform.security.access_control import AccessToken

router = APIRouter(prefix="/pro-lab/ai", tags=["Pro Lab — AI"])


@router.post("/strategy-copilot", response_model=StrategyCopilotResponse)
async def strategy_copilot(
    req: StrategyCopilotRequest,
    _: AccessToken = Depends(require_pro_scope),
    x_pro_lab_test: str | None = Header(default=None, alias="X-Pro-Lab-Test"),
    provider: LLMProvider = Depends(get_ai_provider),
) -> StrategyCopilotResponse:
    del x_pro_lab_test
    return await execute_strategy_copilot(req, provider)


@router.post("/strategy-copilot/stream")
async def strategy_copilot_stream(
    req: StrategyCopilotRequest,
    _: AccessToken = Depends(require_pro_scope),
    provider: LLMProvider = Depends(get_ai_provider),
):
    task = ModelTask(
        task_type="strategy_copilot",
        system_instructions_ref="pro_lab.strategy_copilot.v1",
        messages=(
            ModelMessage(role="system", content=STRATEGY_SYSTEM_PROMPT),
            ModelMessage(
                role="user",
                content=json.dumps(
                    {
                        "idea": req.idea,
                        "market": req.market,
                        "horizon": req.horizon,
                        "risk_budget_pct": req.risk_budget_pct,
                    },
                    ensure_ascii=False,
                ),
            ),
        ),
        settings=ModelSettings(temperature=0.4, response_format="json_object"),
        correlation_id=str(uuid.uuid4()),
        deadline_seconds=20.0,
    )

    async def event_generator():
        emitted_terminal = False
        sequence = 0
        try:
            async for event in with_stream_deadline(provider.stream(task), task):
                sequence = event.sequence + 1
                emitted_terminal = emitted_terminal or event.event in ("completed", "failed", "cancelled")
                yield format_sse_event(event)
                if emitted_terminal:
                    return
        except asyncio.CancelledError:
            raise
        except ModelError as exc:
            if not emitted_terminal:
                yield format_sse_event(
                    StreamEvent(
                        sequence=sequence,
                        event="failed",
                        correlation_id=task.correlation_id,
                        error_code=exc.code,
                        error_message="AI stream failed.",
                    )
                )
        except Exception:
            if not emitted_terminal:
                yield format_sse_event(
                    StreamEvent(
                        sequence=sequence,
                        event="failed",
                        correlation_id=task.correlation_id,
                        error_code="provider_unavailable",
                        error_message="AI stream failed.",
                    )
                )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/swarm-committee", response_model=SwarmCommitteeResponse)
async def swarm_committee(
    req: SwarmCommitteeRequest,
    _: AccessToken = Depends(require_pro_scope),
    provider: LLMProvider = Depends(get_ai_provider),
) -> SwarmCommitteeResponse:
    return await execute_swarm_committee(req, provider)


@router.post("/backtest-critique", response_model=BacktestCritiqueResponse)
async def backtest_critique(
    req: BacktestCritiqueRequest,
    _: AccessToken = Depends(require_pro_scope),
    provider: LLMProvider = Depends(get_ai_provider),
) -> BacktestCritiqueResponse:
    return await execute_backtest_critique(req, provider)


@router.get("/health", response_model=AIHealthResponse)
async def ai_health(
    provider: LLMProvider | None = Depends(get_ai_provider_or_none),
) -> AIHealthResponse:
    if provider is None:
        return AIHealthResponse(configured=False, provider="none", model=None)
    return AIHealthResponse(
        configured=await provider.health(),
        provider=provider.name,
        model=getattr(provider, "default_model", None),
    )
