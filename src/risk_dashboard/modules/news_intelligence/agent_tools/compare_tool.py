from __future__ import annotations

from risk_dashboard.modules.agentic_core.schemas.envelope import TrustedExecutionEnvelope
from risk_dashboard.modules.news_intelligence.agent_tools.helpers import (
    check_scope,
    load_db_articles,
)
from risk_dashboard.modules.news_intelligence.application.clustering import cluster_articles
from risk_dashboard.modules.news_intelligence.domain.entities import utc_now_iso
from risk_dashboard.modules.news_intelligence.domain.ports import SourceRegistryPort
from risk_dashboard.modules.news_intelligence.safety.content_boundary import sanitize_article_content
from risk_dashboard.modules.news_intelligence.schemas.agent_tools import (
    ClaimKind,
    ClaimRow,
    CompareSourcesInput,
    CompareSourcesOutput,
)


async def compare_sources(
    payload: CompareSourcesInput,
    envelope: TrustedExecutionEnvelope,
    registry: SourceRegistryPort | None = None,
) -> CompareSourcesOutput:
    check_scope(envelope, ("public:news:read", "public:news:agent:read"))

    articles = load_db_articles()
    clusters = cluster_articles(articles, limit=50) if articles else []
    target_cluster = next((c for c in clusters if c.cluster_id == payload.cluster_id), None)

    if not target_cluster:
        matched_articles = [a for a in articles if a.article_id == payload.cluster_id]
        if matched_articles:
            target_cluster = cluster_articles(matched_articles, limit=1)[0]

    if not target_cluster:
        raise ValueError(f"NEWS_CLUSTER_NOT_FOUND: Cluster '{payload.cluster_id}' was not found in active pipeline.")

    cluster_articles_list = target_cluster.articles
    claims: list[ClaimRow] = []
    disagreements: list[str] = []
    single_source_claims: list[str] = []

    lead = cluster_articles_list[0]
    topic_claim_id = f"claim_{payload.cluster_id[:8]}_main"
    all_source_ids = tuple(sorted({a.source_id for a in cluster_articles_list}))

    kind: ClaimKind = "fact" if len(all_source_ids) >= 2 else "source_claim"
    if kind == "source_claim":
        single_source_claims.append(topic_claim_id)

    main_claim = ClaimRow(
        claim_id=topic_claim_id,
        kind=kind,
        statement=sanitize_article_content(f"{lead.headline}: {lead.summary}"),
        supporting_source_ids=all_source_ids,
        conflicting_source_ids=(),
        first_seen_at=lead.published_at or utc_now_iso(),
        corroboration_count=len(all_source_ids),
    )
    claims.append(main_claim)

    for a in cluster_articles_list[1:]:
        c_id = f"claim_{a.article_id[:8]}"
        stmt = sanitize_article_content(f"{a.headline}")
        c_kind: ClaimKind = "source_claim"
        if any(w in stmt.lower() for w in ("dự báo", "kỳ vọng", "khả năng", "could", "might", "scenario")):
            c_kind = "hypothesis"

        claims.append(
            ClaimRow(
                claim_id=c_id,
                kind=c_kind,
                statement=stmt,
                supporting_source_ids=(a.source_id,),
                conflicting_source_ids=(),
                first_seen_at=a.published_at or utc_now_iso(),
                corroboration_count=1,
            )
        )
        single_source_claims.append(c_id)

    agreement_rate = 1.0 if not disagreements else max(0.0, 1.0 - (len(disagreements) / max(len(claims), 1)))

    return CompareSourcesOutput(
        schema_version="1.0.0",
        cluster_id=payload.cluster_id,
        claims=tuple(claims),
        agreement_rate=round(agreement_rate, 2),
        disagreements=tuple(disagreements),
        single_source_claims=tuple(single_source_claims),
        evaluated_at=utc_now_iso(),
    )
