from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.0.0"

ImportanceLabel = Literal["critical", "high", "medium", "low", "noise"]
Sentiment = Literal["positive", "neutral", "negative"]
Impact = Literal["high", "medium", "low"]
ThreatLevel = Literal["normal", "watch", "elevated", "critical"]
ClaimKind = Literal["fact", "source_claim", "hypothesis"]
LicenseClass = Literal["open", "attribution_required", "licensed", "restricted"]


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class SourceRef(StrictBaseModel):
    schema_version: str = SCHEMA_VERSION
    source_id: str
    name: str
    url: str
    tier: int = Field(ge=1, le=5)
    region: str
    category: str
    license_class: LicenseClass
    attribution_text: str | None = None


class ArticleRef(StrictBaseModel):
    schema_version: str = SCHEMA_VERSION
    article_id: str
    headline: str
    summary: str
    image_url: str | None = None
    source: SourceRef
    published_at: str
    fetched_at: str
    sort_ts: int
    language: Literal["vi", "en"]
    tickers: tuple[str, ...] = ()
    content_hash: str
    is_untrusted_content: Literal[True] = True


class ImportanceBreakdownOut(StrictBaseModel):
    market_impact: int = Field(ge=0, le=100)
    source_reliability: int = Field(ge=0, le=100)
    freshness: int = Field(ge=0, le=100)
    novelty: int = Field(ge=0, le=100)
    severity: int = Field(ge=0, le=100)
    breadth: int = Field(ge=0, le=100)


class ImportanceOut(StrictBaseModel):
    schema_version: str = SCHEMA_VERSION
    score: int = Field(ge=0, le=100)
    label: ImportanceLabel
    breakdown: ImportanceBreakdownOut
    method_version: str


class SourceHealthRow(StrictBaseModel):
    source: SourceRef
    is_available: bool
    last_success_at: str | None = None
    staleness_minutes: int = Field(ge=0)
    error_rate_24h: float = Field(ge=0.0, le=1.0)
    quality_flag: Literal["ok", "degraded", "unreliable"]
    redistribution_allowed: bool


class ClaimRow(StrictBaseModel):
    claim_id: str
    kind: ClaimKind
    statement: str
    supporting_source_ids: tuple[str, ...]
    conflicting_source_ids: tuple[str, ...] = ()
    first_seen_at: str
    corroboration_count: int = Field(ge=1)


class EvidenceRow(StrictBaseModel):
    claim_id: str
    statement: str
    kind: ClaimKind
    source_ids: tuple[str, ...]
    article_ids: tuple[str, ...]
    published_at: str
    freshness: Literal["current", "stale", "unknown"]


class NewsEvidenceBriefArtifact(StrictBaseModel):
    schema_version: str = SCHEMA_VERSION
    brief_id: str
    artifact_id: str
    authoring_run_id: str
    account_id: str
    title: str
    objective: str
    cluster_ids: tuple[str, ...]
    evidence_rows: tuple[EvidenceRow, ...]
    source_coverage: float = Field(ge=0.0, le=1.0)
    limitations: tuple[str, ...] = ()
    review_status: Literal["reviewed", "rejected", "expired"]
    evidence_hash: str
    version: int = Field(ge=1)
    created_at: str
    expires_at: str
