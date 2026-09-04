from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class ToolExecutionContext(BaseModel):
    account_id: str
    surface: str
    resource_id: str | None = None
    locale: str = "vi-VN"


class ToolResultPayload(BaseModel):
    success: bool = True
    source: str
    source_version: str = "1.0.0"
    freshness: str = "latest"
    provenance_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    summary: str = ""
    warnings: tuple[str, ...] = ()
    error: str | None = None

