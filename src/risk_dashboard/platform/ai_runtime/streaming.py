from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator, Sequence
from typing import Any

from risk_dashboard.platform.ai_runtime.contracts import (
    ModelError,
    ModelResult,
    ModelTask,
    StreamEvent,
    TokenUsage,
)
from risk_dashboard.platform.ai_runtime.structured import parse_structured


class StreamingCollector:
    """Collects stream events into an aggregated ModelResult."""

    def __init__(self, task: ModelTask, provider_name: str, model_name: str) -> None:
        self.task = task
        self.provider_name = provider_name
        self.model_name = model_name
        self.accumulated_text: list[str] = []
        self.events: list[StreamEvent] = []
        self.terminal_event: StreamEvent | None = None
        self.tool_calls: list[dict[str, Any]] = []
        self.usage: TokenUsage = TokenUsage()
        self.started_at: float = time.monotonic()

    def handle_event(self, event: StreamEvent) -> None:
        self.events.append(event)
        if event.delta:
            self.accumulated_text.append(event.delta)
        if event.tool_calls:
            self.tool_calls.extend(event.tool_calls)
        if event.usage:
            self.usage = event.usage
        if event.event in ("completed", "failed", "cancelled"):
            self.terminal_event = event

    def build_result(self) -> ModelResult:
        full_text = "".join(self.accumulated_text)
        parsed = parse_structured(full_text, self.task.output_schema) if self.task.output_schema else None
        latency_ms = round((time.monotonic() - self.started_at) * 1000)
        finish_reason = (
            self.terminal_event.finish_reason
            if self.terminal_event and self.terminal_event.finish_reason
            else "stop"
        )
        return ModelResult(
            parsed=parsed,
            text=full_text,
            tool_calls=tuple(self.tool_calls),
            usage=self.usage,
            provider=self.provider_name,
            model=self.model_name,
            latency_ms=latency_ms,
            finish_reason=finish_reason,
        )


async def with_stream_deadline(
    stream: AsyncIterator[StreamEvent], task: ModelTask
) -> AsyncIterator[StreamEvent]:
    started = time.monotonic()
    while True:
        remaining = task.deadline_seconds - (time.monotonic() - started)
        if remaining <= 0:
            raise ModelError("deadline_exceeded", "AI stream exceeded deadline.")
        try:
            event = await asyncio.wait_for(anext(stream), timeout=remaining)
        except StopAsyncIteration:
            return
        except asyncio.TimeoutError as exc:
            raise ModelError("deadline_exceeded", "AI stream exceeded deadline.") from exc
        yield event


def validate_stream_sequence(events: Sequence[StreamEvent]) -> None:
    """Validates that stream events follow monotonic ordering and single-terminal invariant."""
    if not events:
        raise ModelError("stream_invalid", "Stream contains no events.")
    for expected_seq, event in enumerate(events):
        if event.sequence != expected_seq:
            raise ModelError(
                "stream_invalid",
                f"Stream sequence mismatch: expected {expected_seq}, got {event.sequence}.",
            )
    terminal_events = [e for e in events if e.event in ("completed", "failed", "cancelled")]
    if len(terminal_events) != 1:
        raise ModelError(
            "stream_invalid",
            f"Stream must have exactly one terminal event, found {len(terminal_events)}.",
        )
    if events[-1] != terminal_events[0]:
        raise ModelError(
            "stream_invalid",
            "Terminal event must be the last event in stream.",
        )
