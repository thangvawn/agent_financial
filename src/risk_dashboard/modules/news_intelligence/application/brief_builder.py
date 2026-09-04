from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from risk_dashboard.modules.news_intelligence.domain.entities import NewsArticle, utc_now_iso
from risk_dashboard.modules.news_intelligence.domain.ports import SourceRegistryPort
from risk_dashboard.modules.news_intelligence.infrastructure.source_registry import get_default_source_registry
from risk_dashboard.modules.news_intelligence.safety.content_boundary import sanitize_article_content
from risk_dashboard.modules.news_intelligence.schemas.agent_tools import (
    BuildBriefEvidenceOutput,
    ClaimKind,
    EvidenceRow,
    NewsEvidenceBriefArtifact,
)


def calculate_evidence_hash(evidence_rows: tuple[EvidenceRow, ...] | list[EvidenceRow]) -> str:
    """Deterministic SHA-256 hash of evidence statements and sources."""
    sorted_rows = sorted(
        evidence_rows,
        key=lambda r: (r.claim_id, r.statement, sorted(r.source_ids)),
    )
    raw_payload = [
        {
            "claim_id": r.claim_id,
            "statement": r.statement,
            "kind": r.kind,
            "source_ids": sorted(r.source_ids),
            "article_ids": sorted(r.article_ids),
            "freshness": r.freshness,
        }
        for r in sorted_rows
    ]
    serialized = json.dumps(raw_payload, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _is_corroborating(a: NewsArticle, b: NewsArticle) -> bool:
    if a.article_id == b.article_id:
        return True
    if a.category == b.category or (a.tickers and b.tickers and set(a.tickers) & set(b.tickers)):
        return True
    tokens_a = set(a.headline.lower().split())
    tokens_b = set(b.headline.lower().split())
    if tokens_a and tokens_b and (tokens_a & tokens_b):
        return True
    return False


def build_evidence_rows_from_articles(
    articles: list[NewsArticle],
    source_registry: SourceRegistryPort | None = None,
) -> tuple[tuple[EvidenceRow, ...], tuple[str, ...], float, tuple[str, ...], str]:
    """Extract verifiable evidence rows, check freshness, and evaluate source coverage."""
    if not articles:
        return (), (), 0.0, ("Không có dữ liệu bài báo được cung cấp.",), utc_now_iso()

    registry = source_registry or get_default_source_registry()
    now_dt = datetime.now(timezone.utc)
    now_iso = now_dt.isoformat()
    expires_at = (now_dt + timedelta(hours=24)).isoformat()

    all_sources = tuple(sorted({a.source_id for a in articles}))
    source_health_records = registry.get_health(all_sources)

    available_sources = [r for r in source_health_records if r.is_available and r.quality_flag != "unreliable"]
    source_coverage = len(available_sources) / max(len(all_sources), 1)

    limitations: list[str] = []
    evidence_rows: list[EvidenceRow] = []
    unresolved_claim_ids: list[str] = []

    # Check staleness
    has_stale_sources = False
    for a in articles:
        try:
            pub_dt = datetime.fromisoformat(a.published_at)
            if (now_dt - pub_dt).total_seconds() > 86400:
                has_stale_sources = True
        except (ValueError, TypeError):
            pass

    if has_stale_sources:
        limitations.append("Một số nguồn tin đã xuất bản hơn 24 giờ trước (freshness: stale).")

    if source_coverage < 0.8:
        limitations.append(f"Độ phủ nguồn tin đạt {round(source_coverage * 100)}% (dưới ngưỡng tối ưu 80%).")

    # 1. Lead statement from top article with semantic corroboration
    lead = articles[0]
    corroborating_arts = [a for a in articles if _is_corroborating(lead, a)]
    lead_sources = tuple(sorted({a.source_id for a in corroborating_arts}))
    lead_article_ids = tuple(sorted({a.article_id for a in corroborating_arts}))
    lead_kind: ClaimKind = "fact" if len(lead_sources) >= 2 else "source_claim"

    sanitized_summary = sanitize_article_content(f"{lead.headline}. {lead.summary}")
    lead_freshness = "stale" if has_stale_sources else "current"

    row_lead = EvidenceRow(
        claim_id=f"claim_{hashlib.sha1(lead.headline.encode('utf-8')).hexdigest()[:10]}",
        statement=sanitized_summary,
        kind=lead_kind,
        source_ids=lead_sources,
        article_ids=lead_article_ids,
        published_at=lead.published_at or now_iso,
        freshness=lead_freshness,
    )
    evidence_rows.append(row_lead)

    # 2. Add systemic threat claim if present
    if lead.threat_level in ("elevated", "critical", "watch"):
        threat_claim_id = f"claim_threat_{lead.article_id[:8]}"
        threat_stmt = f"Cảnh báo rủi ro hệ thống mức độ {lead.threat_level} trong danh mục {lead.category}."
        evidence_rows.append(
            EvidenceRow(
                claim_id=threat_claim_id,
                statement=threat_stmt,
                kind="hypothesis",
                source_ids=(lead.source_id,),
                article_ids=(lead.article_id,),
                published_at=lead.published_at or now_iso,
                freshness="current",
            )
        )

    # 3. Additional article claims
    for idx, art in enumerate(articles[1:4], start=2):
        stmt = sanitize_article_content(f"{art.headline}: {art.summary}")
        kind: ClaimKind = "source_claim"
        if art.threat_level in ("elevated", "critical") or any(kw in art.headline.lower() for kw in ("dự báo", "kỳ vọng", "could", "might")):
            kind = "hypothesis"

        claim_id = f"claim_{hashlib.sha1(art.headline.encode('utf-8')).hexdigest()[:10]}"
        evidence_rows.append(
            EvidenceRow(
                claim_id=claim_id,
                statement=stmt,
                kind=kind,
                source_ids=(art.source_id,),
                article_ids=(art.article_id,),
                published_at=art.published_at or now_iso,
                freshness="current",
            )
        )

    if len(all_sources) == 1:
        limitations.append("Cụm tin chỉ dựa trên 1 nguồn đơn lẻ; các nhận định cần được kiểm chứng thêm.")

    return tuple(evidence_rows), tuple(unresolved_claim_ids), round(source_coverage, 2), tuple(limitations), expires_at


def build_brief(
    evidence: BuildBriefEvidenceOutput,
    title: str,
    objective: str,
    authoring_run_id: str,
    account_id: str,
    cluster_ids: tuple[str, ...],
) -> NewsEvidenceBriefArtifact:
    """Build a validated NewsEvidenceBriefArtifact from evidence rows."""
    now_iso = utc_now_iso()
    ev_hash = calculate_evidence_hash(evidence.evidence_rows)

    brief_id = f"brief_{hashlib.sha1(f'{authoring_run_id}:{ev_hash}'.encode('utf-8')).hexdigest()[:12]}"
    artifact_id = f"art_brief_{brief_id[6:]}"

    return NewsEvidenceBriefArtifact(
        schema_version="1.0.0",
        brief_id=brief_id,
        artifact_id=artifact_id,
        authoring_run_id=authoring_run_id,
        account_id=account_id,
        title=title,
        objective=objective,
        cluster_ids=cluster_ids,
        evidence_rows=evidence.evidence_rows,
        source_coverage=evidence.source_coverage,
        limitations=evidence.limitations,
        review_status="reviewed",
        evidence_hash=ev_hash,
        version=1,
        created_at=now_iso,
        expires_at=evidence.expires_at,
    )
