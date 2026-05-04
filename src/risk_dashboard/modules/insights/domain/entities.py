from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class InsightMetric:
    label: str
    value: str


@dataclass(frozen=True)
class InsightDriver:
    label: str
    value: str
    direction: str = "neutral"


@dataclass(frozen=True)
class InsightCard:
    insight_id: str
    title: str
    level: str
    headline: str
    summary: str
    what_changed: str
    why_it_matters: str
    who_should_care: str
    what_to_learn_next: str
    action_category: str
    action_path: str | None
    caution: str
    freshness_status: str
    freshness_at: str | None
    quality_state: str
    risk_banner: str | None = None
    metrics: list[InsightMetric] = field(default_factory=list)
    drivers: list[InsightDriver] = field(default_factory=list)
