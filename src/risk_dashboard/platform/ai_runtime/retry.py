from __future__ import annotations

import asyncio
import time

from risk_dashboard.platform.ai_runtime.contracts import ModelError, ModelResult, ModelTask
from risk_dashboard.platform.ai_runtime.provider import LLMProvider
from risk_dashboard.platform.ai_runtime.telemetry import record_call

MAX_PROMPT_CHARS: int = 100_000
CIRCUIT_BREAKER_THRESHOLD: int = 5

_circuit_states: dict[str, dict[str, Any]] = {}


def reset_circuit_breaker(provider_name: str | None = None) -> None:
    if provider_name:
        _circuit_states.pop(provider_name, None)
    else:
        _circuit_states.clear()


def _get_breaker(name: str) -> dict[str, Any]:
    if name not in _circuit_states:
        _circuit_states[name] = {"failures": 0, "open": False}
    return _circuit_states[name]


def _record_failure(name: str) -> None:
    b = _get_breaker(name)
    b["failures"] += 1
    if b["failures"] >= CIRCUIT_BREAKER_THRESHOLD:
        b["open"] = True


def _record_success(name: str) -> None:
    b = _get_breaker(name)
    b["failures"] = 0
    b["open"] = False


async def with_retry(
    provider: LLMProvider,
    task: ModelTask,
    *,
    max_retries: int = 2,
) -> ModelResult:
    total_chars = sum(len(m.content) for m in task.messages)
    if total_chars > MAX_PROMPT_CHARS:
        raise ModelError(
            "configuration_error",
            f"Prompt length ({total_chars}) exceeds max allowed {MAX_PROMPT_CHARS}.",
        )

    b = _get_breaker(provider.name)
    if b["open"]:
        raise ModelError(
            "provider_unavailable",
            "Circuit breaker is OPEN due to consecutive failures.",
            retryable=False,
        )

    started = time.monotonic()
    for attempt in range(max_retries + 1):
        remaining = task.deadline_seconds - (time.monotonic() - started)
        if remaining <= 0:
            _record_failure(provider.name)
            raise ModelError("deadline_exceeded", "Model request exceeded deadline.")
        try:
            result = await asyncio.wait_for(provider.generate(task), timeout=remaining)
            _record_success(provider.name)
            record_call(task, result)
            return result
        except asyncio.TimeoutError as exc:
            if attempt == max_retries:
                _record_failure(provider.name)
                raise ModelError("deadline_exceeded", "Model request exceeded deadline.") from exc
        except ModelError as exc:
            if not exc.retryable or attempt == max_retries:
                _record_failure(provider.name)
                raise
            await asyncio.sleep(min(0.25 * (2**attempt), remaining))
        except Exception:
            if attempt == max_retries:
                _record_failure(provider.name)
                raise
    _record_failure(provider.name)
    raise AssertionError("retry loop must return or raise")
