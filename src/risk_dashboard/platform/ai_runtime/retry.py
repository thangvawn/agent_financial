from __future__ import annotations

import asyncio
import time

from risk_dashboard.platform.ai_runtime.contracts import ModelError, ModelResult, ModelTask
from risk_dashboard.platform.ai_runtime.provider import LLMProvider


async def with_retry(
    provider: LLMProvider,
    task: ModelTask,
    *,
    max_retries: int = 2,
) -> ModelResult:
    started = time.monotonic()
    for attempt in range(max_retries + 1):
        remaining = task.deadline_seconds - (time.monotonic() - started)
        if remaining <= 0:
            raise ModelError("deadline_exceeded", "Model request exceeded deadline.")
        try:
            return await asyncio.wait_for(provider.generate(task), timeout=remaining)
        except asyncio.TimeoutError as exc:
            raise ModelError("deadline_exceeded", "Model request exceeded deadline.") from exc
        except ModelError as exc:
            if not exc.retryable or attempt == max_retries:
                raise
            await asyncio.sleep(min(0.25 * (2**attempt), remaining))
    raise AssertionError("retry loop must return or raise")
