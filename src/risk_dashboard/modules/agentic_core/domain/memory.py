from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

PROHIBITED_PATTERNS = [
    re.compile(r"chain-of-thought", re.IGNORECASE),
    re.compile(r"thought:\s", re.IGNORECASE),
    re.compile(r"api_key|api_secret|sk-[a-zA-Z0-9_\-]+", re.IGNORECASE),
    re.compile(r"raw tool payload", re.IGNORECASE),
    re.compile(r"<\s*/?\s*untrusted_context\s*>", re.IGNORECASE),
    re.compile(r"\b(buy|sell)\b.*\b(stock|shares|immediately|market price|portfolio)\b", re.IGNORECASE),
    re.compile(r"bank balance|account balance|private report", re.IGNORECASE),
]

VALID_PROVENANCES = {"user_stated", "user_approved_plan", "deterministic_checkpoint"}
VALID_MEMORY_TYPES = {"preference", "goal", "plan", "mastery", "misconception"}


class MemoryItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0.0"
    memory_id: str
    account_id: str
    run_id: str | None = None
    memory_type: str
    content: str
    provenance: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    sensitivity: str = "normal"
    ttl_days: int | None = None
    expires_at: str | None = None
    created_at: str
    updated_at: str
