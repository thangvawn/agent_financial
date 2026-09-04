from __future__ import annotations

from typing import Any
from risk_dashboard.modules.agentic_core.domain.tools import RiskClass, ToolManifest

GET_CLUSTER_MANIFEST = ToolManifest(
    tool_id="news.get_cluster",
    name="Get News Cluster",
    module="news_intelligence",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Fetch a cluster of related news articles by cluster_id, including lead article and importance score.",
    required_capabilities=("public:news:read",),
)

GET_SOURCE_HEALTH_MANIFEST = ToolManifest(
    tool_id="news.get_source_health",
    name="Get News Source Health",
    module="news_intelligence",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Evaluate the health, freshness, licensing, and availability of news sources.",
    required_capabilities=("public:news:read",),
)

GET_ENRICHMENT_MANIFEST = ToolManifest(
    tool_id="news.get_enrichment",
    name="Get Article Enrichment",
    module="news_intelligence",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Retrieve deterministic enrichment metadata for an article.",
    required_capabilities=("public:news:read",),
)

COMPARE_SOURCES_MANIFEST = ToolManifest(
    tool_id="news.compare_sources",
    name="Compare Sources Agreement",
    module="news_intelligence",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Generate a source agreement/disagreement matrix and classify claims into fact, source_claim, or hypothesis.",
    required_capabilities=("public:news:read",),
)

GET_MARKET_CONTEXT_MANIFEST = ToolManifest(
    tool_id="news.get_market_context",
    name="Get Market Context",
    module="news_intelligence",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Fetch deterministic market context from market_summary.",
    required_capabilities=("public:market_summary:read",),
)

BUILD_BRIEF_EVIDENCE_MANIFEST = ToolManifest(
    tool_id="news.build_brief_evidence",
    name="Build Brief Evidence",
    module="news_intelligence",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Aggregate verified evidence rows, source coverage, and limitations across clusters for a brief objective.",
    required_capabilities=("public:news:read",),
)

SAVE_BRIEF_MANIFEST = ToolManifest(
    tool_id="news.save_brief",
    name="Save Evidence Brief Confirmed",
    module="news_intelligence",
    risk_class=RiskClass.CONFIRMED_WRITE,
    version="1.0.0",
    description="Persist a reviewed NewsEvidenceBrief artifact upon explicit human confirmation and hash validation.",
    required_capabilities=("public:news:write",),
)

CAPABILITY_MANIFEST: dict[str, Any] = {
    "capability_id": "news.evidence_brief.v1",
    "entry_modes": ["embedded", "conversational"],
    "required_scopes": ["public:news:read"],
    "allowed_tools": [
        "news.get_cluster",
        "news.get_source_health",
        "news.get_enrichment",
        "news.compare_sources",
        "news.get_market_context",
        "news.build_brief_evidence",
    ],
    "max_tool_calls": 8,
    "risk_class": "read",
    "artifact_type": "news_evidence_brief.v1",
    "action_policy": "save_requires_confirmation",
    "feature_flag": "module.news_intelligence.agent.enabled",
}


def get_news_tool_manifests() -> tuple[ToolManifest, ...]:
    return (
        GET_CLUSTER_MANIFEST,
        GET_SOURCE_HEALTH_MANIFEST,
        GET_ENRICHMENT_MANIFEST,
        COMPARE_SOURCES_MANIFEST,
        GET_MARKET_CONTEXT_MANIFEST,
        BUILD_BRIEF_EVIDENCE_MANIFEST,
        SAVE_BRIEF_MANIFEST,
    )

