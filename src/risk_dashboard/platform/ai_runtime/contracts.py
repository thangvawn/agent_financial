from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

Role = Literal["system", "user", "assistant", "tool"]
StreamEventType = Literal["start", "token", "tool_call", "completed", "failed", "cancelled"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ModelMessage(BaseModel):
    role: Role
    content: str


class ModelSettings(BaseModel):
    temperature: float = Field(default=0.4, ge=0, le=2)
    max_output_tokens: int = Field(default=4096, ge=1)
    response_format: Literal["text", "json_object"] = "json_object"


class ModelTask(BaseModel):
    schema_version: str = "1.0.0"
    task_type: str
    system_instructions_ref: str
    messages: tuple[ModelMessage, ...]
    tool_schemas: tuple[dict[str, Any], ...] = ()
    output_schema: dict[str, Any] | None = None
    settings: ModelSettings = Field(default_factory=ModelSettings)
    correlation_id: str
    deadline_seconds: float = Field(default=20.0, gt=0)
    max_cost_usd: float = Field(default=0.10, ge=0)


class TokenUsage(BaseModel):
    prompt: int = Field(default=0, ge=0)
    completion: int = Field(default=0, ge=0)
    total: int = Field(default=0, ge=0)


class ModelResult(BaseModel):
    schema_version: str = "1.0.0"
    parsed: dict[str, Any] | None = None
    text: str
    tool_calls: tuple[dict[str, Any], ...] = ()
    usage: TokenUsage = Field(default_factory=TokenUsage)
    provider: str
    model: str
    latency_ms: int = Field(ge=0)
    finish_reason: str
    repair_attempts: int = Field(default=0, ge=0)


class StreamEvent(BaseModel):
    schema_version: str = "1.0.0"
    sequence: int = Field(ge=0)
    event: StreamEventType
    correlation_id: str
    run_id: str | None = None
    delta: str = ""
    tool_calls: tuple[dict[str, Any], ...] = ()
    parsed: dict[str, Any] | None = None
    usage: TokenUsage | None = None
    error_code: str | None = None
    error_message: str | None = None
    finish_reason: str | None = None
    created_at: str = Field(default_factory=_utc_now_iso)


class ModelError(Exception):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable
