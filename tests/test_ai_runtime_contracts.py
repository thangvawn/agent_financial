from __future__ import annotations

import pytest

from risk_dashboard.platform.ai_runtime.contracts import (
    ModelError,
    ModelMessage,
    ModelResult,
    ModelTask,
    TokenUsage,
)
from risk_dashboard.platform.ai_runtime.redaction import redact_for_provider
from risk_dashboard.platform.ai_runtime.structured import parse_structured


def _task() -> ModelTask:
    return ModelTask(
        task_type="tutor_answer",
        system_instructions_ref="tutor.v1",
        messages=(ModelMessage(role="user", content="answer"),),
        correlation_id="correlation-1",
    )


def test_model_contracts_round_trip() -> None:
    task = _task()
    result = ModelResult(
        text='{"answer":"ok"}',
        parsed={"answer": "ok"},
        usage=TokenUsage(prompt=2, completion=3, total=5),
        provider="fake",
        model="fake-model",
        latency_ms=1,
        finish_reason="stop",
    )
    assert ModelTask.model_validate_json(task.model_dump_json()) == task
    assert ModelResult.model_validate_json(result.model_dump_json()) == result


def test_structured_output_and_redaction() -> None:
    assert parse_structured('```json\n{"answer":"ok"}\n```', {"required": ["answer"]}) == {
        "answer": "ok"
    }
    task = _task().model_copy(
        update={"messages": (ModelMessage(role="user", content="token=secret-value"),)}
    )
    assert "secret-value" not in redact_for_provider(task).messages[0].content
    with pytest.raises(ModelError, match="valid JSON"):
        parse_structured("not-json")
    with pytest.raises(ModelError, match="output schema"):
        parse_structured('{"answer": 1}', {"properties": {"answer": {"type": "string"}}})
