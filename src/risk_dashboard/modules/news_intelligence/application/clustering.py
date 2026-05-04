from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

from risk_dashboard.modules.news_intelligence.domain.entities import NewsArticle


STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "are",
    "was",
    "into",
    "over",
    "after",
    "amid",
}


@dataclass
class NewsCluster:
    cluster_id: str
    lead_article: NewsArticle
    articles: list[NewsArticle]
    similarity_topic: str
    velocity: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "lead_article": self.lead_article.to_dict(),
            "article_count": len(self.articles),
            "source_count": len({article.source_id for article in self.articles}),
            "category": self.lead_article.category,
            "sentiment": self.lead_article.sentiment,
            "impact": self.lead_article.impact,
            "velocity": self.velocity,
            "is_breaking": self.velocity == "fast" and self.lead_article.priority >= 4,
            "related_articles": [article.to_dict() for article in self.articles[1:5]],
            "similarity_topic": self.similarity_topic,
            # ── New fields ──
            "importance_score": max((a.importance_score for a in self.articles), default=0),
            "importance_label": self.lead_article.importance_label,
            "affected_markets": sorted(set(
                market for a in self.articles for market in a.affected_markets
            ))[:6],
            "cluster_summary": _cluster_summary(self),
        }


def cluster_articles(articles: list[NewsArticle], *, limit: int = 20) -> list[NewsCluster]:
    sorted_articles = sorted(articles, key=lambda item: (item.source_tier, -item.sort_ts))
    clusters: list[list[NewsArticle]] = []

    for article in sorted_articles:
        article_tokens = _tokens(article.headline)
        placed = False
        for cluster in clusters:
            lead = cluster[0]
            if abs(article.sort_ts - lead.sort_ts) > 24 * 3600:
                continue
            threshold = 0.22 if article.category == lead.category else 0.32
            if _jaccard(article_tokens, _tokens(lead.headline)) >= threshold:
                cluster.append(article)
                placed = True
                break
        if not placed:
            clusters.append([article])

    output: list[NewsCluster] = []
    for cluster in clusters:
        ranked = sorted(cluster, key=lambda item: (-item.importance_score, item.source_tier, -item.priority, -item.sort_ts))
        output.append(
            NewsCluster(
                cluster_id=_cluster_id(ranked),
                lead_article=ranked[0],
                articles=ranked,
                similarity_topic=_topic_label(ranked[0].headline),
                velocity=_velocity(ranked),
            )
        )
    return sorted(output, key=lambda item: (item.lead_article.importance_score, len(item.articles), item.lead_article.priority, item.lead_article.sort_ts), reverse=True)[:limit]


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(token) > 2 and token not in STOP_WORDS}


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _cluster_id(articles: list[NewsArticle]) -> str:
    raw = "|".join(sorted(article.article_id for article in articles))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _topic_label(headline: str) -> str:
    tokens = list(_tokens(headline))
    return " ".join(tokens[:4]) if tokens else "market update"


def _velocity(articles: list[NewsArticle]) -> str:
    if len(articles) >= 3:
        return "fast"
    if len(articles) == 2:
        return "building"
    return "single"


def _cluster_summary(cluster: NewsCluster) -> str:
    """Generate a brief summary for the cluster."""
    article_count = len(cluster.articles)
    source_count = len({a.source_id for a in cluster.articles})
    lead = cluster.lead_article
    parts = [f"{article_count} bài từ {source_count} nguồn"]
    if lead.importance_label in ("critical", "high"):
        parts.append(f"importance: {lead.importance_label}")
    if lead.sentiment != "neutral":
        parts.append(f"sentiment: {lead.sentiment}")
    return " · ".join(parts)
