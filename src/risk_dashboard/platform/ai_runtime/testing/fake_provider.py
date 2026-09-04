from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import AsyncIterator, Mapping, Sequence

from risk_dashboard.platform.ai_runtime.contracts import (
    ModelError,
    ModelResult,
    ModelTask,
    StreamEvent,
    TokenUsage,
)
from risk_dashboard.platform.ai_runtime.structured import parse_structured

ScriptedResponse = ModelResult | ModelError
ScriptedStream = Sequence[str] | ModelError


class FakeProvider:
    name = "fake"
    default_model = "fake-model"

    def __init__(
        self,
        scripted: Sequence[ScriptedResponse] = (),
        *,
        by_task_type: Mapping[str, ScriptedResponse] | None = None,
        scripted_streams: Sequence[ScriptedStream] = (),
        by_task_type_stream: Mapping[str, ScriptedStream] | None = None,
        delay_seconds: float = 0,
    ) -> None:
        self._scripted = deque(scripted)
        self._by_task_type = dict(by_task_type or {})
        self._scripted_streams = deque(scripted_streams)
        self._by_task_type_stream = dict(by_task_type_stream or {})
        self.delay_seconds = delay_seconds

    async def generate(self, task: ModelTask) -> ModelResult:
        if self.delay_seconds:
            await asyncio.sleep(self.delay_seconds)
        response = self._by_task_type.get(task.task_type)
        if response is None:
            if not self._scripted:
                raise ModelError("provider_unavailable", "Fake provider has no scripted response.")
            response = self._scripted.popleft()
        if isinstance(response, ModelError):
            raise response
        return response

    async def stream(self, task: ModelTask) -> AsyncIterator[StreamEvent]:
        stream_spec = self._by_task_type_stream.get(task.task_type)
        if stream_spec is None:
            if self._scripted_streams:
                stream_spec = self._scripted_streams.popleft()
            elif task.task_type in self._by_task_type:
                res = self._by_task_type[task.task_type]
                if isinstance(res, ModelError):
                    stream_spec = res
                else:
                    stream_spec = [res.text]
            elif self._scripted:
                res = self._scripted.popleft()
                if isinstance(res, ModelError):
                    stream_spec = res
                else:
                    stream_spec = [res.text]
            else:
                stream_spec = ["ok"]

        seq = 0
        yield StreamEvent(
            sequence=seq,
            event="start",
            correlation_id=task.correlation_id,
        )
        seq += 1

        if isinstance(stream_spec, ModelError):
            raise stream_spec

        accumulated: list[str] = []
        try:
            for chunk in stream_spec:
                if self.delay_seconds:
                    await asyncio.sleep(self.delay_seconds)
                accumulated.append(chunk)
                yield StreamEvent(
                    sequence=seq,
                    event="token",
                    correlation_id=task.correlation_id,
                    delta=chunk,
                )
                seq += 1
        except (ModelError, asyncio.CancelledError):
            raise

        full_text = "".join(accumulated)
        parsed = None
        if task.output_schema and full_text:
            try:
                parsed = parse_structured(full_text, task.output_schema)
            except Exception:
                pass

        yield StreamEvent(
            sequence=seq,
            event="completed",
            correlation_id=task.correlation_id,
            parsed=parsed,
            usage=TokenUsage(
                prompt=len(task.messages) * 10,
                completion=len(accumulated) * 5,
                total=len(task.messages) * 10 + len(accumulated) * 5,
            ),
            finish_reason="stop",
        )

    async def health(self) -> bool:
        return True
