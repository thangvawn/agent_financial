from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from risk_dashboard.platform.ai_runtime.contracts import ModelResult, ModelTask, StreamEvent


class LLMProvider(Protocol):
    name: str
    default_model: str

    async def generate(self, task: ModelTask) -> ModelResult: ...

    async def stream(self, task: ModelTask) -> AsyncIterator[StreamEvent]: ...

    async def health(self) -> bool: ...
