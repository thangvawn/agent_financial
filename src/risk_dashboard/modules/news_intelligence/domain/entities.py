from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class NewsSource:
    source_id: str
    name: str
    url: str
    category: str
    region: str
    tier: int
    flag: str
    source_group: str = "global"


@dataclass
class NewsArticle:
    article_id: str
    headline: str
    summary: str
    source: str
    source_id: str
    source_tier: int
    source_flag: str
    region: str
    category: str
    url: str
    published_at: str
    fetched_at: str
    sort_ts: int
    priority: int = 3
    sentiment: str = "neutral"
    impact: str = "medium"
    tickers: list[str] = field(default_factory=list)
    language: str = "en"
    threat_level: str = "normal"
    threat_category: str | None = None
    threat_confidence: float = 0.0
    # ── New fields (Sprint 1) ──
    importance_score: int = 0
    importance_label: str = "noise"
    importance_breakdown: dict[str, int] = field(default_factory=dict)
    source_mix: str = ""
    content_hash: str = ""
    affected_markets: list[str] = field(default_factory=list)
    affected_sectors: list[str] = field(default_factory=list)
    what_to_monitor: list[str] = field(default_factory=list)
    learn_links: list[dict[str, str]] = field(default_factory=list)
    related_entities: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        time_label = self.published_at[11:16] if "T" in self.published_at else ""
        return {
            "id": self.article_id,
            "article_id": self.article_id,
            "time": time_label,
            "headline": self.headline,
            "summary": self.summary,
            "source": self.source,
            "source_id": self.source_id,
            "source_tier": self.source_tier,
            "source_flag": self.source_flag,
            "region": self.region,
            "category": self.category,
            "url": self.url,
            "published_at": self.published_at,
            "fetched_at": self.fetched_at,
            "sort_ts": self.sort_ts,
            "priority": self.priority,
            "sentiment": self.sentiment,
            "impact": self.impact,
            "tickers": self.tickers,
            "language": self.language,
            "threat_level": self.threat_level,
            "threat_category": self.threat_category,
            "threat_confidence": self.threat_confidence,
            "importance_score": self.importance_score,
            "importance_label": self.importance_label,
            "importance_breakdown": self.importance_breakdown,
            "source_mix": self.source_mix,
            "affected_markets": self.affected_markets,
            "affected_sectors": self.affected_sectors,
            "what_to_monitor": self.what_to_monitor,
            "learn_links": self.learn_links,
            "related_entities": self.related_entities,
        }
