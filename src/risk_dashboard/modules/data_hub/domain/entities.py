from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class TopicPolicy:
    topic: str
    ttl_seconds: int
    min_interval_seconds: int
    priority: int
    source: str


@dataclass(frozen=True)
class TopicSnapshot:
    topic: str
    payload: dict[str, Any]
    freshness: str
    confidence_label: str
    source: str
    last_success_at: str
    ttl_seconds: int
    stale_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "payload": self.payload,
            "freshness": self.freshness,
            "confidence_label": self.confidence_label,
            "source": self.source,
            "last_success_at": self.last_success_at,
            "ttl_seconds": self.ttl_seconds,
            "stale_reason": self.stale_reason,
        }
