"""News Importance Scoring.

Computes a 0–100 importance score for each article/event based on:
  General = 0.35×MarketImpact + 0.20×SourceReliability + 0.15×Freshness
            + 0.10×Novelty + 0.10×Severity + 0.10×Breadth

Score labels:
  85–100 Critical | 70–84 High | 50–69 Medium | 30–49 Low | <30 Noise
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from risk_dashboard.modules.news_intelligence.domain.enums import importance_label_for_score


@dataclass(frozen=True)
class ImportanceBreakdown:
    market_impact: int
    source_reliability: int
    freshness: int
    novelty: int
    severity: int
    breadth: int

    def to_dict(self) -> dict[str, int]:
        return {
            "market_impact": self.market_impact,
            "source_reliability": self.source_reliability,
            "freshness": self.freshness,
            "novelty": self.novelty,
            "severity": self.severity,
            "breadth": self.breadth,
        }


@dataclass(frozen=True)
class ImportanceResult:
    score: int
    label: str
    breakdown: ImportanceBreakdown

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "label": self.label,
            "breakdown": self.breakdown.to_dict(),
        }


# ── Scoring weights (General user) ─────────────────────────────────────

_W_MARKET_IMPACT = 0.35
_W_SOURCE_RELIABILITY = 0.20
_W_FRESHNESS = 0.15
_W_NOVELTY = 0.10
_W_SEVERITY = 0.10
_W_BREADTH = 0.10

# ── High-impact keyword sets ───────────────────────────────────────────

_HIGH_IMPACT_KEYWORDS = frozenset({
    "fed", "fomc", "rate", "rates", "inflation", "cpi", "gdp",
    "recession", "war", "sanctions", "tariff", "default", "crisis",
    "oil", "opec", "gold", "bitcoin", "earnings", "sec", "ecb",
    "imf", "pboc", "boj", "rba",
})
_SYSTEMIC_KEYWORDS = frozenset({
    "crisis", "default", "bank run", "sanction", "invasion",
    "recession", "liquidity", "contagion", "collapse",
})
_BROAD_KEYWORDS = frozenset({
    "global", "worldwide", "all markets", "broad-based",
    "systemic", "across sectors",
})


def calculate_importance(
    *,
    headline: str,
    summary: str,
    source_tier: int,
    impact: str,
    sentiment: str,
    threat_level: str,
    age_minutes: float,
    cluster_size: int = 1,
    is_duplicate: bool = False,
) -> ImportanceResult:
    """Calculate importance score (0–100) for a news article."""
    text = f"{headline} {summary}".lower()

    market_impact = _score_market_impact(text, impact, sentiment)
    source_reliability = _score_source_reliability(source_tier)
    freshness = _score_freshness(age_minutes)
    novelty = _score_novelty(is_duplicate, cluster_size)
    severity = _score_severity(text, threat_level)
    breadth = _score_breadth(text, cluster_size)

    raw = (
        _W_MARKET_IMPACT * market_impact
        + _W_SOURCE_RELIABILITY * source_reliability
        + _W_FRESHNESS * freshness
        + _W_NOVELTY * novelty
        + _W_SEVERITY * severity
        + _W_BREADTH * breadth
    )
    score = max(0, min(100, round(raw)))
    label = importance_label_for_score(score)

    return ImportanceResult(
        score=score,
        label=label,
        breakdown=ImportanceBreakdown(
            market_impact=market_impact,
            source_reliability=source_reliability,
            freshness=freshness,
            novelty=novelty,
            severity=severity,
            breadth=breadth,
        ),
    )


def _score_market_impact(text: str, impact: str, sentiment: str) -> int:
    """0–100 based on keyword presence and impact/sentiment labels."""
    base = 30
    hit_count = sum(1 for kw in _HIGH_IMPACT_KEYWORDS if kw in text)
    base += min(hit_count * 8, 40)
    if impact == "high":
        base += 20
    elif impact == "medium":
        base += 10
    if sentiment in ("negative", "positive"):
        base += 5
    return min(100, base)


def _score_source_reliability(source_tier: int) -> int:
    """0–100 based on source tier (1=official, 2=major media, 3+=specialist)."""
    if source_tier <= 1:
        return 95
    if source_tier == 2:
        return 75
    if source_tier == 3:
        return 55
    return 35


def _score_freshness(age_minutes: float) -> int:
    """0–100 based on article age. Newer = higher."""
    if age_minutes <= 30:
        return 100
    if age_minutes <= 120:
        return 85
    if age_minutes <= 360:
        return 70
    if age_minutes <= 720:
        return 55
    if age_minutes <= 1440:
        return 40
    if age_minutes <= 4320:
        return 25
    return 10


def _score_novelty(is_duplicate: bool, cluster_size: int) -> int:
    """0–100 based on whether article adds new information."""
    if is_duplicate:
        return 10
    if cluster_size >= 5:
        return 40  # Many sources → story is covered, less novel
    if cluster_size >= 2:
        return 60  # Confirmed but still developing
    return 85  # First/only source → potentially novel


def _score_severity(text: str, threat_level: str) -> int:
    """0–100 based on systemic risk language."""
    base = 20
    hits = sum(1 for kw in _SYSTEMIC_KEYWORDS if kw in text)
    base += min(hits * 15, 45)
    if threat_level == "elevated":
        base += 25
    elif threat_level == "watch":
        base += 15
    elif threat_level == "critical":
        base += 35
    return min(100, base)


def _score_breadth(text: str, cluster_size: int) -> int:
    """0–100 based on how broadly the event affects markets."""
    base = 20
    hits = sum(1 for kw in _BROAD_KEYWORDS if kw in text)
    base += min(hits * 12, 36)
    if cluster_size >= 4:
        base += 25
    elif cluster_size >= 2:
        base += 15
    return min(100, base)
