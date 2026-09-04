from __future__ import annotations

from typing import Literal

from risk_dashboard.modules.agentic_core.schemas.envelope import TrustedExecutionEnvelope
from risk_dashboard.modules.news_intelligence.agent_tools.helpers import (
    check_scope,
    load_db_articles,
)
from risk_dashboard.modules.news_intelligence.domain.entities import utc_now_iso
from risk_dashboard.modules.news_intelligence.domain.ports import SourceRegistryPort
from risk_dashboard.modules.news_intelligence.infrastructure.source_registry import get_default_source_registry
from risk_dashboard.modules.news_intelligence.schemas.agent_tools import (
    GetEnrichmentInput,
    GetEnrichmentOutput,
    GetSourceHealthInput,
    GetSourceHealthOutput,
    Impact,
    ImportanceBreakdownOut,
    ImportanceLabel,
    ImportanceOut,
    Sentiment,
    SourceHealthRow,
    SourceRef,
    ThreatLevel,
)


async def get_source_health(
    payload: GetSourceHealthInput,
    envelope: TrustedExecutionEnvelope,
    registry: SourceRegistryPort | None = None,
) -> GetSourceHealthOutput:
    check_scope(envelope, ("public:news:read", "public:news:agent:read"))
    source_reg = registry or get_default_source_registry()

    records = source_reg.get_health(payload.source_ids)
    coverage_sufficient = source_reg.evaluate_coverage(payload.source_ids)

    rows: list[SourceHealthRow] = []
    for r in records:
        source_ref = source_reg.get_source(r.source_id)
        if not source_ref:
            source_ref = SourceRef(
                source_id=r.source_id,
                name=r.name,
                url="https://example.com",
                tier=r.tier,
                region=r.region,
                category=r.category,
                license_class=r.license_class,
                attribution_text=r.attribution_text,
            )
        rows.append(
            SourceHealthRow(
                source=source_ref,
                is_available=r.is_available,
                last_success_at=r.last_success_at,
                staleness_minutes=r.staleness_minutes,
                error_rate_24h=r.error_rate_24h,
                quality_flag=r.quality_flag,
                redistribution_allowed=r.redistribution_allowed,
            )
        )

    return GetSourceHealthOutput(
        schema_version="1.0.0",
        rows=tuple(rows),
        evaluated_at=utc_now_iso(),
        coverage_sufficient=coverage_sufficient,
    )


async def get_enrichment(
    payload: GetEnrichmentInput,
    envelope: TrustedExecutionEnvelope,
) -> GetEnrichmentOutput:
    check_scope(envelope, ("public:news:read", "public:news:agent:read"))

    articles = load_db_articles()
    matched = [a for a in articles if a.article_id == payload.article_id]
    if not matched:
        raise ValueError(f"NEWS_ARTICLE_NOT_FOUND: Article '{payload.article_id}' was not found in active pipeline.")

    article = matched[0]
    bd_dict = article.importance_breakdown
    breakdown = ImportanceBreakdownOut(
        market_impact=bd_dict.get("market_impact", 50),
        source_reliability=bd_dict.get("source_reliability", 80),
        freshness=bd_dict.get("freshness", 90),
        novelty=bd_dict.get("novelty", 70),
        severity=bd_dict.get("severity", 30),
        breadth=bd_dict.get("breadth", 60),
    )
    lbl: ImportanceLabel = "medium"
    if article.importance_label in ("critical", "high", "medium", "low", "noise"):
        lbl = article.importance_label  # type: ignore

    importance = ImportanceOut(
        schema_version="1.0.0",
        score=article.importance_score,
        label=lbl,
        breakdown=breakdown,
        method_version="1.0.0",
    )

    sentiment_val: Sentiment = article.sentiment if article.sentiment in ("positive", "neutral", "negative") else "neutral"
    impact_val: Impact = article.impact if article.impact in ("high", "medium", "low") else "medium"
    threat_val: ThreatLevel = (
        article.threat_level if article.threat_level in ("normal", "watch", "elevated", "critical") else "normal"
    )

    return GetEnrichmentOutput(
        schema_version="1.0.0",
        article_id=article.article_id,
        sentiment=sentiment_val,
        impact=impact_val,
        priority=min(5, max(1, article.priority)),
        category=article.category,
        threat_level=threat_val,
        threat_category=article.threat_category,
        threat_confidence=float(article.threat_confidence),
        tickers=tuple(article.tickers),
        importance=importance,
        affected_markets=tuple(article.affected_markets),
        affected_sectors=tuple(article.affected_sectors),
        what_to_monitor=tuple(article.what_to_monitor),
        learn_links=tuple(article.learn_links),
        related_entities=tuple(article.related_entities),
        enrichment_method_version="1.0.0",
    )
