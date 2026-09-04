from __future__ import annotations

import asyncio
import time
from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from risk_dashboard.modules.agentic_core.application.tool_grants import resolve_grant
from risk_dashboard.modules.agentic_core.domain.ports import ReadOnlyTool
from risk_dashboard.modules.agentic_core.domain.tools import RiskClass, ToolGrant
from risk_dashboard.modules.agentic_core.schemas.envelope import TrustedExecutionEnvelope
from risk_dashboard.platform.ai_runtime.contracts import ModelError, ModelTask
from risk_dashboard.platform.ai_runtime.provider import LLMProvider
from risk_dashboard.platform.ai_runtime.telemetry import calculate_cost_usd

GraphStatus = Literal["success", "recovery"]


class GraphResult(TypedDict):
    status: GraphStatus
    code: str | None
    text: str | None
    evidence: dict[str, str] | None
    trace: tuple[str, ...]
    steps_used: int
    tool_calls_used: int
    tokens_used: int
    cost_used: float


class _GraphState(TypedDict):
    envelope: TrustedExecutionEnvelope
    task: ModelTask
    provider: LLMProvider
    tool: ReadOnlyTool
    started_at: float
    trace: tuple[str, ...]
    steps_used: int
    tool_calls_used: int
    tokens_used: int
    cost_used: float
    grant: ToolGrant | None
    evidence: dict[str, str] | None
    text: str | None
    code: str | None


def _advance(state: _GraphState, node: str) -> dict[str, object]:
    return {
        "trace": (*state["trace"], node),
        "steps_used": state["steps_used"] + 1,
    }


def _recovery(state: _GraphState, code: str) -> dict[str, object]:
    update = _advance(state, "recovery")
    update["code"] = code
    return update


def _estimate_prompt_tokens(task: ModelTask) -> int:
    chars = sum(len(m.content) for m in task.messages) + len(task.system_instructions_ref or "")
    return max(1, (chars + 3) // 4)


def _guard(state: _GraphState) -> dict[str, object]:
    envelope = state["envelope"]
    if state["steps_used"] >= envelope.budget.max_steps:
        return _recovery(state, "step_budget_exhausted")
    if time.monotonic() - state["started_at"] >= envelope.budget.max_wall_seconds:
        return _recovery(state, "wall_budget_exhausted")
    if state["tool_calls_used"] >= envelope.budget.max_tool_calls:
        return _recovery(state, "tool_budget_exhausted")
    if envelope.budget.max_tokens <= 0:
        return _recovery(state, "token_budget_exhausted")
    if envelope.budget.max_cost_usd <= 0:
        return _recovery(state, "cost_budget_exhausted")

    prompt_tokens = _estimate_prompt_tokens(state["task"])
    if envelope.budget.max_tokens > 0 and prompt_tokens >= envelope.budget.max_tokens:
        return _recovery(state, "token_budget_exhausted")

    model_name = getattr(state["provider"], "default_model", "gemini-3.5-flash")
    if envelope.budget.max_cost_usd > 0:
        est_cost = calculate_cost_usd(model_name, prompt_tokens, 0)
        if est_cost >= envelope.budget.max_cost_usd:
            return _recovery(state, "cost_budget_exhausted")

    return _advance(state, "guard")


def _route_after_guard(state: _GraphState) -> Literal["router", "recovery"]:
    return "recovery" if state["code"] else "router"


def _router(state: _GraphState) -> dict[str, object]:
    if state["task"].task_type != "agentic_read":
        return _recovery(state, "unknown_task_type")
    return _advance(state, "router")


def _route_after_router(state: _GraphState) -> Literal["specialist", "recovery"]:
    return "recovery" if state["code"] else "specialist"


def _route_after_specialist(state: _GraphState) -> Literal["reviewer", "recovery"]:
    return "recovery" if state["code"] else "reviewer"


def _remaining_wall_seconds(state: _GraphState) -> float:
    return state["envelope"].budget.max_wall_seconds - (time.monotonic() - state["started_at"])


async def _specialist(state: _GraphState) -> dict[str, object]:
    tool = state["tool"]
    if tool.manifest.risk_class is not RiskClass.READ:
        return _recovery(state, "tool_not_granted")
    grant = resolve_grant(state["envelope"], tool.manifest)
    if grant is None:
        return _recovery(state, "tool_not_granted")
    remaining = _remaining_wall_seconds(state)
    if remaining <= 0:
        return _recovery(state, "wall_budget_exhausted")
    tool_calls_used = state["tool_calls_used"] + 1
    try:
        evidence = await asyncio.wait_for(tool.execute(grant), timeout=remaining)
    except asyncio.TimeoutError:
        update = _recovery(state, "wall_budget_exhausted")
        update["tool_calls_used"] = tool_calls_used
        return update
    except Exception:  # pragma: no cover - tool implementations own detail
        update = _recovery(state, "tool_failed")
        update["tool_calls_used"] = tool_calls_used
        return update
    update = _advance(state, "specialist")
    update.update(
        {
            "grant": grant,
            "evidence": evidence,
            "tool_calls_used": tool_calls_used,
        }
    )
    return update


async def _reviewer(state: _GraphState) -> dict[str, object]:
    envelope = state["envelope"]
    task = state["task"]
    provider = state["provider"]
    model_name = getattr(provider, "default_model", "gemini-3.5-flash")

    cumulative_tokens = state.get("tokens_used", 0)
    cumulative_cost = state.get("cost_used", 0.0)

    max_attempts = 3
    last_error_code = "model_call_failed"
    result = None

    for attempt in range(max_attempts):
        remaining_wall = _remaining_wall_seconds(state)
        if remaining_wall <= 0:
            return _recovery(state, "wall_budget_exhausted")

        # 1. Run-level remaining budget check
        rem_tokens = envelope.budget.max_tokens - cumulative_tokens
        rem_cost = envelope.budget.max_cost_usd - cumulative_cost

        if envelope.budget.max_tokens > 0 and rem_tokens <= 0:
            return _recovery(state, "token_budget_exhausted")
        if envelope.budget.max_cost_usd > 0 and rem_cost <= 0:
            return _recovery(state, "cost_budget_exhausted")

        # 2. Pre-dispatch prompt reservation for this attempt
        prompt_tokens = _estimate_prompt_tokens(task)
        if envelope.budget.max_tokens > 0 and prompt_tokens >= rem_tokens:
            return _recovery(state, "token_budget_exhausted")

        est_prompt_cost = calculate_cost_usd(model_name, prompt_tokens, 0)
        if envelope.budget.max_cost_usd > 0 and est_prompt_cost >= rem_cost:
            return _recovery(state, "cost_budget_exhausted")

        available_output_tokens = rem_tokens - prompt_tokens if envelope.budget.max_tokens > 0 else 4096
        if envelope.budget.max_tokens > 0 and available_output_tokens <= 0:
            return _recovery(state, "token_budget_exhausted")

        available_output_cost = rem_cost - est_prompt_cost if envelope.budget.max_cost_usd > 0 else 100.0
        if envelope.budget.max_cost_usd > 0 and available_output_cost <= 0:
            return _recovery(state, "cost_budget_exhausted")

        # Clamp task settings for this specific attempt
        attempt_max_output = min(task.settings.max_output_tokens, available_output_tokens)
        new_settings = task.settings.model_copy(update={"max_output_tokens": max(1, attempt_max_output)})
        attempt_task = task.model_copy(
            update={
                "settings": new_settings,
                "max_cost_usd": min(task.max_cost_usd, available_output_cost),
            }
        )

        # 3. Dispatch attempt with timeout
        try:
            attempt_result = await asyncio.wait_for(provider.generate(attempt_task), timeout=remaining_wall)
        except asyncio.TimeoutError:
            return _recovery(state, "wall_budget_exhausted")
        except ModelError as exc:
            cumulative_tokens += prompt_tokens
            cumulative_cost += est_prompt_cost
            last_error_code = exc.code
            if not exc.retryable or attempt == max_attempts - 1:
                return _recovery(state, last_error_code)
            await asyncio.sleep(min(0.05 * (2**attempt), max(0.01, remaining_wall)))
            continue
        except Exception:
            cumulative_tokens += prompt_tokens
            cumulative_cost += est_prompt_cost
            if attempt == max_attempts - 1:
                return _recovery(state, "model_call_failed")
            await asyncio.sleep(min(0.05 * (2**attempt), max(0.01, remaining_wall)))
            continue

        # 4. Usage reconciliation & Fail-closed on zero/missing usage with non-empty text
        text = attempt_result.text or ""
        usage = attempt_result.usage

        if usage is None or (usage.total == 0 and text.strip()):
            derived_comp_tokens = max(1, (len(text) + 3) // 4)
            actual_prompt_tokens = prompt_tokens
            actual_comp_tokens = derived_comp_tokens
            actual_total_tokens = actual_prompt_tokens + actual_comp_tokens
        else:
            actual_prompt_tokens = usage.prompt or prompt_tokens
            actual_comp_tokens = usage.completion or 0
            actual_total_tokens = max(usage.total or 0, actual_prompt_tokens + actual_comp_tokens)

        actual_cost = calculate_cost_usd(model_name, actual_prompt_tokens, actual_comp_tokens)

        cumulative_tokens += actual_total_tokens
        cumulative_cost += actual_cost

        # 5. Check run-level budget after attempt
        if envelope.budget.max_tokens > 0 and cumulative_tokens > envelope.budget.max_tokens:
            return _recovery(state, "token_budget_exhausted")
        if envelope.budget.max_cost_usd > 0 and cumulative_cost > envelope.budget.max_cost_usd:
            return _recovery(state, "cost_budget_exhausted")

        result = attempt_result
        break

    if result is None:
        return _recovery(state, last_error_code)

    update = _advance(state, "reviewer")
    update["text"] = result.text
    update["tokens_used"] = cumulative_tokens
    update["cost_used"] = cumulative_cost
    return update


def _route_after_reviewer(state: _GraphState) -> Literal["success", "recovery"]:
    return "recovery" if state["code"] else "success"


def _success(state: _GraphState) -> dict[str, object]:
    return _advance(state, "success")


def _build_graph():
    graph = StateGraph(_GraphState)
    graph.add_node("guard", _guard)
    graph.add_node("router", _router)
    graph.add_node("specialist", _specialist)
    graph.add_node("reviewer", _reviewer)
    graph.add_node("success", _success)
    graph.add_node("recovery", lambda state: _advance(state, "recovery"))
    graph.add_edge(START, "guard")
    graph.add_conditional_edges("guard", _route_after_guard)
    graph.add_conditional_edges("router", _route_after_router)
    graph.add_conditional_edges("specialist", _route_after_specialist)
    graph.add_conditional_edges("reviewer", _route_after_reviewer)
    graph.add_edge("success", END)
    graph.add_edge("recovery", END)
    return graph.compile()


async def run_graph(
    envelope: TrustedExecutionEnvelope,
    task: ModelTask,
    provider: LLMProvider,
    tool: ReadOnlyTool,
) -> GraphResult:
    compiled = _build_graph()
    initial_state: _GraphState = {
        "envelope": envelope,
        "task": task,
        "provider": provider,
        "tool": tool,
        "started_at": time.monotonic(),
        "trace": (),
        "steps_used": 0,
        "tool_calls_used": 0,
        "tokens_used": 0,
        "cost_used": 0.0,
        "grant": None,
        "evidence": None,
        "text": None,
        "code": None,
    }
    state = await compiled.ainvoke(initial_state)
    status: GraphStatus = "recovery" if state.get("code") else "success"
    return {
        "status": status,
        "code": state.get("code"),
        "text": state.get("text"),
        "evidence": state.get("evidence"),
        "trace": state.get("trace", ()),
        "steps_used": state.get("steps_used", 0),
        "tool_calls_used": state.get("tool_calls_used", 0),
        "tokens_used": state.get("tokens_used", 0),
        "cost_used": state.get("cost_used", 0.0),
    }
