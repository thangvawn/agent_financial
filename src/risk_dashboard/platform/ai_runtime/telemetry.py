from __future__ import annotations

from risk_dashboard.platform.ai_runtime.contracts import ModelResult, ModelTask

_usage_summary = {
    "calls": 0,
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0,
    "estimated_cost_usd": 0.0,
}

_latencies_ms: list[int] = []

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
    _latencies_ms.append(result.latency_ms)
    return {
        "provider": result.provider,
        "model": result.model,
        "latency_ms": result.latency_ms,
        "finish_reason": result.finish_reason,
        "total_tokens": result.usage.total,
        "cost_usd": cost,
    }


def get_latency_stats() -> dict[str, float]:
    """Calculate p50, p95, p99, and average latency in milliseconds (§8)."""
    if not _latencies_ms:
        return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "avg": 0.0, "max": 0.0, "count": 0}
    sorted_lat = sorted(_latencies_ms)
    n = len(sorted_lat)
    p50_idx = max(0, int((0.50 * n) + 0.5) - 1)
    p95_idx = max(0, int((0.95 * n) + 0.5) - 1)
    p99_idx = max(0, int((0.99 * n) + 0.5) - 1)
    return {
        "p50": float(sorted_lat[min(p50_idx, n - 1)]),
        "p95": float(sorted_lat[min(p95_idx, n - 1)]),
        "p99": float(sorted_lat[min(p99_idx, n - 1)]),
        "avg": round(sum(sorted_lat) / n, 2),
        "max": float(sorted_lat[-1]),
        "count": n,
    }


def evaluate_alert_rules(
    *,
    max_p95_latency_ms: float | None = None,
    max_cost_usd: float | None = None,
    max_calls: int | None = None,
) -> list[str]:
    """Evaluate telemetry against performance and cost alert rules (§6.1, §8)."""
    triggered: list[str] = []
    stats = get_latency_stats()
    if max_p95_latency_ms is not None and stats["p95"] > max_p95_latency_ms:
        triggered.append(
            f"ALERT_LATENCY_P95_EXCEEDED: p95 latency {stats['p95']}ms exceeds {max_p95_latency_ms}ms"
        )
    cost = _usage_summary["estimated_cost_usd"]
    if max_cost_usd is not None and cost > max_cost_usd:
        triggered.append(
            f"ALERT_COST_BUDGET_EXCEEDED: cost ${cost} exceeds budget ${max_cost_usd}"
        )
    calls = _usage_summary["calls"]
    if max_calls is not None and calls > max_calls:
        triggered.append(
            f"ALERT_CALL_VOLUME_EXCEEDED: call count {calls} exceeds limit {max_calls}"
        )
    return triggered


def get_usage_summary() -> dict[str, int | float]:
    return dict(_usage_summary)


def reset_usage_summary() -> None:
    _usage_summary["calls"] = 0
    _usage_summary["prompt_tokens"] = 0
    _usage_summary["completion_tokens"] = 0
    _usage_summary["total_tokens"] = 0
    _usage_summary["estimated_cost_usd"] = 0.0
    _latencies_ms.clear()

