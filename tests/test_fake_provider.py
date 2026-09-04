from __future__ import annotations

import asyncio

import pytest

from risk_dashboard.platform.ai_runtime.contracts import ModelError, ModelMessage, ModelResult, ModelTask
from risk_dashboard.platform.ai_runtime.testing.fake_provider import FakeProvider


def _task(task_type: str = "answer") -> ModelTask:
    return ModelTask(
        task_type=task_type,
        system_instructions_ref="test.v1",
        messages=(ModelMessage(role="user", content="test"),),
        correlation_id="correlation-1",
    )


def _result(text: str = "ok") -> ModelResult:
    return ModelResult(
        text=text,
        provider="fake",
        model="fake-model",
        latency_ms=0,
        finish_reason="stop",
    )


def test_fake_provider_returns_scripted_response() -> None:
    provider = FakeProvider([_result()])
    assert asyncio.run(provider.generate(_task())).text == "ok"
    assert asyncio.run(provider.health())


def test_fake_provider_supports_task_type_and_errors() -> None:
    provider = FakeProvider(by_task_type={"special": _result("special")})
    assert asyncio.run(provider.generate(_task("special"))).text == "special"
    failed = FakeProvider([ModelError("rate_limited", "retry", retryable=True)])
    with pytest.raises(ModelError, match="retry"):
        asyncio.run(failed.generate(_task()))
