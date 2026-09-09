from __future__ import annotations

import asyncio
import uuid

import pytest

from risk_dashboard.platform.ai_runtime.contracts import (
    ModelError,
    ModelMessage,
    ModelSettings,
    ModelTask,
    StreamEvent,
)
from risk_dashboard.platform.ai_runtime.sse import format_sse_event, parse_sse_frame
from risk_dashboard.platform.ai_runtime.streaming import (
    StreamingCollector,
    validate_stream_sequence,
    with_stream_deadline,
)
from risk_dashboard.platform.ai_runtime.testing.fake_provider import FakeProvider



def _sample_task() -> ModelTask:
    return ModelTask(
        task_type="strategy_copilot",
        system_instructions_ref="pro_lab.strategy_copilot.v1",
        messages=(
            ModelMessage(role="system", content="You are an assistant."),
            ModelMessage(role="user", content="Draft a momentum strategy."),
        ),
        settings=ModelSettings(temperature=0.4, response_format="json_object"),
        correlation_id=str(uuid.uuid4()),
        deadline_seconds=10.0,
    )


def test_fake_provider_ordered_stream_events():
    async def _test():
        task = _sample_task()
        provider = FakeProvider(
            scripted_streams=[["{\"strategy_name\": ", "\"Momentum Alpha\", ", "\"universe\": [\"FPT\"]}"]],
        )
        events: list[StreamEvent] = []
        async for event in provider.stream(task):
            events.append(event)

        assert len(events) >= 3
        assert events[0].event == "start"
        assert events[0].sequence == 0
        assert events[-1].event == "completed"
        assert events[-1].sequence == len(events) - 1

        validate_stream_sequence(events)

    asyncio.run(_test())


def test_streaming_collector_aggregates_into_model_result():
    async def _test():
        task = _sample_task()
        provider = FakeProvider(
            scripted_streams=[["{\"strategy_name\": \"FPT Trend\", \"confidence\": \"high\"}"]],
        )
        collector = StreamingCollector(task, provider_name="fake", model_name="fake-model")
        async for event in provider.stream(task):
            collector.handle_event(event)

        result = collector.build_result()
        assert "FPT Trend" in result.text
        assert result.provider == "fake"
        assert result.model == "fake-model"
        assert result.finish_reason == "stop"

    asyncio.run(_test())


def test_stream_error_handling():
    async def _test():
        task = _sample_task()
        provider = FakeProvider(
            scripted_streams=[ModelError("provider_unavailable", "Service down", retryable=True)]
        )
        events: list[StreamEvent] = []
        with pytest.raises(ModelError, match="Service down"):
            async for event in provider.stream(task):
                events.append(event)

        assert len(events) == 1
        assert events[0].event == "start"

    asyncio.run(_test())


def test_stream_cancellation_propagation():
    async def _test():
        task = _sample_task()
        provider = FakeProvider(
            scripted_streams=[["chunk1", "chunk2", "chunk3", "chunk4"]],
            delay_seconds=0.01,
        )
        events: list[StreamEvent] = []

        async def consume_and_cancel():
            stream_iter = provider.stream(task)
            async for event in stream_iter:
                events.append(event)
                if event.event == "token":
                    raise asyncio.CancelledError()

        with pytest.raises(asyncio.CancelledError):
            await consume_and_cancel()

        assert any(e.event == "start" for e in events)
        assert any(e.event == "token" for e in events)

    asyncio.run(_test())


def test_sse_formatting_and_parsing():
    event = StreamEvent(
        sequence=1,
        event="token",
        correlation_id="corr-123",
        delta="hello world",
    )
    frame = format_sse_event(event)
    assert frame.startswith("event: token\n")
    assert "data: " in frame
    assert frame.endswith("\n\n")

    parsed = parse_sse_frame(frame)
    assert parsed is not None
    assert parsed["event"] == "token"
    assert parsed["data"]["sequence"] == 1
    assert parsed["data"]["delta"] == "hello world"
    assert parsed["data"]["correlation_id"] == "corr-123"


def test_stream_deadline_is_enforced_for_delayed_provider():
    async def _test():
        task = _sample_task().model_copy(update={"deadline_seconds": 0.005})
        provider = FakeProvider(scripted_streams=[["late1", "late2"]], delay_seconds=0.05)
        events: list[StreamEvent] = []
        with pytest.raises(ModelError) as exc_info:
            async for event in with_stream_deadline(provider.stream(task), task):
                events.append(event)

        assert exc_info.value.code == "deadline_exceeded"
        assert events[0].event == "start"
        assert all(e.event != "cancelled" for e in events)

    asyncio.run(_test())

