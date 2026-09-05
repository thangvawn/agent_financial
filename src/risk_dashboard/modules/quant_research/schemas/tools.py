"""Tool execution schemas for quant_research module."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class QuantSourceRefV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    source_type: Literal["panel", "model", "benchmark", "engine"]
    version: str
    as_of: datetime | None = None


class QuantToolResultV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0.0"] = "1.0.0"
    tool_name: str
    status: Literal["ok", "partial", "unavailable"]
    payload: dict[str, Any]
    source_refs: tuple[QuantSourceRefV1, ...]
    warnings: tuple[str, ...] = ()
    generated_at: datetime

