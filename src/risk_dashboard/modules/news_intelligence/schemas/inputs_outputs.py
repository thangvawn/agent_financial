from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

from risk_dashboard.modules.news_intelligence.schemas.models import (
    SCHEMA_VERSION,
    ArticleRef,
    ClaimRow,
    EvidenceRow,
    Impact,
    ImportanceOut,
    Sentiment,
    SourceHealthRow,
    StrictBaseModel,
    ThreatLevel,
)


class GetClusterInput(StrictBaseModel):
    schema_version: str = SCHEMA_VERSION
    cluster_id: str
    max_articles: int = Field(default=8, ge=1, le=20)


class GetClusterOutput(StrictBaseModel):
    schema_version: str = SCHEMA_VERSION
    cluster_id: str
    similarity_topic: str
    velocity: Literal["fast", "steady", "slow"]
    article_count: int = Field(ge=1)
    source_count: int = Field(ge=1)
    is_breaking: bool
    lead_article: ArticleRef
    articles: tuple[ArticleRef, ...]
    importance: ImportanceOut
    window_start: str
    window_end: str


class GetSourceHealthInput(StrictBaseModel):
    schema_version: str = SCHEMA_VERSION
    source_ids: tuple[str, ...] = ()


class GetSourceHealthOutput(StrictBaseModel):
    schema_version: str = SCHEMA_VERSION
    rows: tuple[SourceHealthRow, ...]
    evaluated_at: str
    coverage_sufficient: bool


class GetEnrichmentInput(StrictBaseModel):
    schema_version: str = SCHEMA_VERSION
    article_id: str


class GetEnrichmentOutput(StrictBaseModel):
    schema_version: str = SCHEMA_VERSION
    article_id: str
    sentiment: Sentiment
    impact: Impact
    priority: int = Field(ge=1, le=5)
    category: str
    threat_level: ThreatLevel
    threat_category: str | None = None
    threat_confidence: float = Field(ge=0.0, le=1.0)
    tickers: tuple[str, ...] = ()
    importance: ImportanceOut
    affected_markets: tuple[str, ...] = ()
    affected_sectors: tuple[str, ...] = ()
    what_to_monitor: tuple[str, ...] = ()
    learn_links: tuple[dict[str, str], ...] = ()
    related_entities: tuple[dict[str, str], ...] = ()
    enrichment_method_version: str


class CompareSourcesInput(StrictBaseModel):
    schema_version: str = SCHEMA_VERSION
    cluster_id: str


class CompareSourcesOutput(StrictBaseModel):
    schema_version: str = SCHEMA_VERSION
    cluster_id: str
    claims: tuple[ClaimRow, ...]
    agreement_rate: float = Field(ge=0.0, le=1.0)
    disagreements: tuple[str, ...] = ()
    single_source_claims: tuple[str, ...] = ()
    evaluated_at: str


class GetMarketContextInput(StrictBaseModel):
    schema_version: str = SCHEMA_VERSION
    event_time: str
    markets: tuple[str, ...] = ()


class GetMarketContextOutput(StrictBaseModel):
    schema_version: str = SCHEMA_VERSION
    as_of: str
    session_state: Literal["pre_open", "open", "closed", "holiday"]
    index_metrics: tuple[dict[str, Any], ...] = ()
    breadth: dict[str, Any] | None = None
    capital_flow: dict[str, Any] | None = None
    data_quality: Literal["complete", "partial", "stale", "unavailable"]
    provenance: dict[str, str]
    time_aligned: bool


class BuildBriefEvidenceInput(StrictBaseModel):
    schema_version: str = SCHEMA_VERSION
    cluster_ids: tuple[str, ...] = Field(min_length=1, max_length=5)
    objective: str = Field(min_length=1, max_length=500)


class BuildBriefEvidenceOutput(StrictBaseModel):
    schema_version: str = SCHEMA_VERSION
    evidence_rows: tuple[EvidenceRow, ...]
    unresolved_claim_ids: tuple[str, ...] = ()
    source_coverage: float = Field(ge=0.0, le=1.0)
    limitations: tuple[str, ...] = ()
    expires_at: str


class SaveBriefInput(StrictBaseModel):
    schema_version: str = SCHEMA_VERSION
    proposal_id: str
    evidence_hash: str
    title: str = Field(min_length=1, max_length=160)
    objective: str = Field(min_length=1, max_length=500)
    cluster_ids: tuple[str, ...] = ()
    evidence_rows: tuple[EvidenceRow, ...]
    limitations: tuple[str, ...] = ()


class SaveBriefOutput(StrictBaseModel):
    schema_version: str = SCHEMA_VERSION
    brief_id: str
    artifact_id: str
    receipt_id: str
    version: int = Field(ge=1)
    status: Literal["saved"] = "saved"
    created_at: str
    expires_at: str
