from __future__ import annotations

from typing import Literal

from risk_dashboard.modules.agentic_core.schemas.envelope import TrustedExecutionEnvelope
from risk_dashboard.modules.news_intelligence.agent_tools.helpers import (
    article_to_ref,
    check_scope,
    load_db_articles,
)
from risk_dashboard.modules.news_intelligence.application.clustering import NewsCluster, cluster_articles
from risk_dashboard.modules.news_intelligence.domain.entities import utc_now_iso
from risk_dashboard.modules.news_intelligence.domain.ports import SourceRegistryPort
from risk_dashboard.modules.news_intelligence.infrastructure.source_registry import get_default_source_registry
from risk_dashboard.modules.news_intelligence.schemas.agent_tools import (
    GetClusterInput,
    GetClusterOutput,
    ImportanceBreakdownOut,
    ImportanceLabel,
    ImportanceOut,
)


async def get_cluster(
    payload: GetClusterInput,
    envelope: TrustedExecutionEnvelope,
    registry: SourceRegistryPort | None = None,
) -> GetClusterOutput:
    check_scope(envelope, ("public:news:read", "public:news:agent:read"))
    source_reg = registry or get_default_source_registry()

    articles = load_db_articles()
    clusters = cluster_articles(articles, limit=50) if articles else []
    target_cluster: NewsCluster | None = next((c for c in clusters if c.cluster_id == payload.cluster_id), None)

    if not target_cluster:
        matched_articles = [a for a in articles if a.article_id == payload.cluster_id]
        if matched_articles:
            target_cluster = cluster_articles(matched_articles, limit=1)[0]

    if not target_cluster:
        raise ValueError(f"NEWS_CLUSTER_NOT_FOUND: Cluster '{payload.cluster_id}' was not found in active pipeline.")

    limit_articles = target_cluster.articles[: payload.max_articles]
    article_refs = tuple(article_to_ref(a, source_reg) for a in limit_articles)
    lead_ref = article_to_ref(target_cluster.lead_article, source_reg)

    bd_dict = target_cluster.lead_article.importance_breakdown
    breakdown = ImportanceBreakdownOut(
        market_impact=bd_dict.get("market_impact", 50),
        source_reliability=bd_dict.get("source_reliability", 70),
        freshness=bd_dict.get("freshness", 80),
        novelty=bd_dict.get("novelty", 60),
        severity=bd_dict.get("severity", 40),
        breadth=bd_dict.get("breadth", 50),
    )
    lbl: ImportanceLabel = "medium"
    if target_cluster.lead_article.importance_label in ("critical", "high", "medium", "low", "noise"):
        lbl = target_cluster.lead_article.importance_label  # type: ignore

    importance = ImportanceOut(
        schema_version="1.0.0",
        score=target_cluster.lead_article.importance_score,
        label=lbl,
        breakdown=breakdown,
        method_version="1.0.0",
    )

    window_times = [a.published_at for a in limit_articles if a.published_at]
    w_start = min(window_times) if window_times else utc_now_iso()
    w_end = max(window_times) if window_times else utc_now_iso()
    vel: Literal["fast", "steady", "slow"] = (
        target_cluster.velocity if target_cluster.velocity in ("fast", "steady", "slow") else "steady"
    )

    return GetClusterOutput(
        schema_version="1.0.0",
        cluster_id=target_cluster.cluster_id,
        similarity_topic=target_cluster.similarity_topic,
        velocity=vel,
        article_count=len(target_cluster.articles),
        source_count=len({a.source_id for a in target_cluster.articles}),
        is_breaking=target_cluster.velocity == "fast" and target_cluster.lead_article.priority >= 4,
        lead_article=lead_ref,
        articles=article_refs,
        importance=importance,
        window_start=w_start,
        window_end=w_end,
    )
