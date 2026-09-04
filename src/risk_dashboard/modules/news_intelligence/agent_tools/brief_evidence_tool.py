from __future__ import annotations

from risk_dashboard.modules.agentic_core.schemas.envelope import TrustedExecutionEnvelope
from risk_dashboard.modules.news_intelligence.agent_tools.helpers import (
    check_scope,
    load_db_articles,
)
from risk_dashboard.modules.news_intelligence.application.brief_builder import build_evidence_rows_from_articles
from risk_dashboard.modules.news_intelligence.domain.entities import NewsArticle
from risk_dashboard.modules.news_intelligence.domain.ports import SourceRegistryPort
from risk_dashboard.modules.news_intelligence.infrastructure.source_registry import get_default_source_registry
from risk_dashboard.modules.news_intelligence.schemas.agent_tools import (
    BuildBriefEvidenceInput,
    BuildBriefEvidenceOutput,
)


async def build_brief_evidence(
    payload: BuildBriefEvidenceInput,
    envelope: TrustedExecutionEnvelope,
    registry: SourceRegistryPort | None = None,
) -> BuildBriefEvidenceOutput:
    check_scope(envelope, ("public:news:read", "public:news:agent:read"))
    source_reg = registry or get_default_source_registry()

    articles = load_db_articles()
    selected_articles: list[NewsArticle] = []

    for cid in payload.cluster_ids:
        c_arts = [a for a in articles if a.article_id == cid or cid in a.category]
        if c_arts:
            selected_articles.extend(c_arts)

    if not selected_articles:
        raise ValueError(
            f"NEWS_CLUSTER_NOT_FOUND: None of requested cluster_ids {payload.cluster_ids} were found in active pipeline."
        )

    evidence_rows, unresolved, coverage, limitations, expires_at = build_evidence_rows_from_articles(
        selected_articles, source_registry=source_reg
    )

    return BuildBriefEvidenceOutput(
        schema_version="1.0.0",
        evidence_rows=evidence_rows,
        unresolved_claim_ids=unresolved,
        source_coverage=coverage,
        limitations=limitations,
        expires_at=expires_at,
    )
