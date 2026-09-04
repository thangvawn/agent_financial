from __future__ import annotations

from risk_dashboard.platform.ai_runtime.contracts import ModelResult, ModelTask

_usage_summary = {
    "calls": 0,
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0,
    "estimated_cost_usd": 0.0,
}

_MODEL_RATES = {
    "gemini-3.5-flash": {"prompt_per_1m": 0.075, "completion_per_1m": 0.30},
}


def calculate_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    rates = _MODEL_RATES.get(model, {"prompt_per_1m": 0.075, "completion_per_1m": 0.30})
    prompt_cost = (prompt_tokens / 1_000_000) * rates["prompt_per_1m"]
    completion_cost = (completion_tokens / 1_000_000) * rates["completion_per_1m"]
    return round(prompt_cost + completion_cost, 6)


def record_call(task: ModelTask, result: ModelResult) -> dict[str, int | str | float]:
    del task
    cost = calculate_cost_usd(result.model, result.usage.prompt, result.usage.completion)
    _usage_summary["calls"] += 1
    _usage_summary["prompt_tokens"] += result.usage.prompt
    _usage_summary["completion_tokens"] += result.usage.completion
    _usage_summary["total_tokens"] += result.usage.total
    _usage_summary["estimated_cost_usd"] = round(_usage_summary["estimated_cost_usd"] + cost, 6)
    return {
        "provider": result.provider,
        "model": result.model,
        "latency_ms": result.latency_ms,
        "finish_reason": result.finish_reason,
        "total_tokens": result.usage.total,
        "cost_usd": cost,
    }


def get_usage_summary() -> dict[str, int | float]:
    return dict(_usage_summary)


def reset_usage_summary() -> None:
    _usage_summary["calls"] = 0
    _usage_summary["prompt_tokens"] = 0
    _usage_summary["completion_tokens"] = 0
    _usage_summary["total_tokens"] = 0
    _usage_summary["estimated_cost_usd"] = 0.0
