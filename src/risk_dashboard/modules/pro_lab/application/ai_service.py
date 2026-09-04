"""Application service orchestrating AI tasks for Pro Lab."""
from __future__ import annotations

import json
import uuid

from fastapi import HTTPException

from risk_dashboard.modules.pro_lab.api.ai_helpers import handle_model_error, parse_json_payload
from risk_dashboard.modules.pro_lab.api.ai_prompts import (
    BACKTEST_SYSTEM_PROMPT,
    STRATEGY_SYSTEM_PROMPT,
    SWARM_SYSTEM_PROMPT,
)
from risk_dashboard.modules.pro_lab.schemas.ai import (
    BacktestCritiqueRequest,
    BacktestCritiqueResponse,
    StrategyCopilotRequest,
    StrategyCopilotResponse,
    SwarmAgentMemo,
    SwarmCommitteeRequest,
    SwarmCommitteeResponse,
)
from risk_dashboard.platform.ai_runtime.contracts import (
    ModelMessage,
    ModelSettings,
    ModelTask,
)
from risk_dashboard.platform.ai_runtime.provider import LLMProvider
from risk_dashboard.platform.ai_runtime.retry import with_retry


async def execute_strategy_copilot(
    req: StrategyCopilotRequest,
    provider: LLMProvider,
) -> StrategyCopilotResponse:
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
    try:
        result = await with_retry(provider, task)
    except Exception as exc:
        handle_model_error(exc)
        raise

    payload = parse_json_payload(result.text, result.parsed)
    try:
        return StrategyCopilotResponse(
            strategy_name=str(payload.get("strategy_name", "Untitled strategy"))[:80],
            market=str(payload.get("market", req.market))[:80],
            universe=[str(item)[:20] for item in (payload.get("universe") or [])][:8],
            signal_stack=[str(item)[:200] for item in (payload.get("signal_stack") or [])][:6],
            risk_rules=[str(item)[:200] for item in (payload.get("risk_rules") or [])][:6],
            validation_queue=[str(item)[:200] for item in (payload.get("validation_queue") or [])][:6],
            rationale=str(payload.get("rationale", ""))[:500],
            horizon=str(payload.get("horizon", req.horizon))[:40],
            confidence=str(payload.get("confidence", "medium")).lower()[:10],
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"AI payload không hợp lệ: {exc}") from exc


async def execute_swarm_committee(
    req: SwarmCommitteeRequest,
    provider: LLMProvider,
) -> SwarmCommitteeResponse:
    task = ModelTask(
        task_type="swarm_committee",
        system_instructions_ref="pro_lab.swarm_committee.v1",
        messages=(
            ModelMessage(role="system", content=SWARM_SYSTEM_PROMPT),
            ModelMessage(
                role="user",
                content=json.dumps(
                    {
                        "strategy_brief": req.strategy_brief,
                        "review_focus": req.review_focus,
                        "market": req.market,
                    },
                    ensure_ascii=False,
                ),
            ),
        ),
        settings=ModelSettings(temperature=0.4, response_format="json_object"),
        correlation_id=str(uuid.uuid4()),
        deadline_seconds=20.0,
    )
    try:
        result = await with_retry(provider, task)
    except Exception as exc:
        handle_model_error(exc)
        raise

    payload = parse_json_payload(result.text, result.parsed)
    try:
        memos_raw = payload.get("memos") or []
        memos = [
            SwarmAgentMemo(
                role=str(m.get("role", "Unknown"))[:50],
                stance=str(m.get("stance", "cautious"))[:30],
                memo=str(m.get("memo", ""))[:600],
                key_concerns=[str(c)[:200] for c in (m.get("key_concerns") or [])][:5],
            )
            for m in memos_raw[:4]
        ]
        return SwarmCommitteeResponse(
            consensus=str(payload.get("consensus", "hold"))[:30],
            confidence=str(payload.get("confidence", "medium"))[:10],
            memos=memos,
            decision_summary=str(payload.get("decision_summary", ""))[:500],
            next_actions=[str(a)[:200] for a in (payload.get("next_actions") or [])][:6],
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"AI payload không hợp lệ: {exc}") from exc


async def execute_backtest_critique(
    req: BacktestCritiqueRequest,
    provider: LLMProvider,
) -> BacktestCritiqueResponse:
    task = ModelTask(
        task_type="backtest_critique",
        system_instructions_ref="pro_lab.backtest_critique.v1",
        messages=(
            ModelMessage(role="system", content=BACKTEST_SYSTEM_PROMPT),
            ModelMessage(role="user", content=json.dumps(req.model_dump(), ensure_ascii=False)),
        ),
        settings=ModelSettings(temperature=0.4, response_format="json_object"),
        correlation_id=str(uuid.uuid4()),
        deadline_seconds=20.0,
    )
    try:
        result = await with_retry(provider, task)
    except Exception as exc:
        handle_model_error(exc)
        raise

    payload = parse_json_payload(result.text, result.parsed)
    try:
        return BacktestCritiqueResponse(
            overall_grade=str(payload.get("overall_grade", "C"))[:5],
            red_flags=[str(x)[:200] for x in (payload.get("red_flags") or [])][:6],
            strengths=[str(x)[:200] for x in (payload.get("strengths") or [])][:6],
            additional_validation=[str(x)[:200] for x in (payload.get("additional_validation") or [])][:6],
            interpretation=str(payload.get("interpretation", ""))[:600],
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"AI payload không hợp lệ: {exc}") from exc

