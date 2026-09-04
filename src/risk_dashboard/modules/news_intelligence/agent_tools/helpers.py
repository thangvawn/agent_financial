from __future__ import annotations

import hashlib
import json
import logging
from typing import Literal

from risk_dashboard.modules.agentic_core.schemas.envelope import TrustedExecutionEnvelope
from risk_dashboard.modules.news_intelligence.domain.entities import NewsArticle
from risk_dashboard.modules.news_intelligence.domain.ports import SourceRegistryPort
from risk_dashboard.modules.news_intelligence.safety.content_boundary import sanitize_article_content
from risk_dashboard.modules.news_intelligence.schemas.agent_tools import (
    ArticleRef,
    SourceRef,
)
from risk_dashboard.platform.database import open_app_state_db

logger = logging.getLogger(__name__)


def check_scope(envelope: TrustedExecutionEnvelope, required_scopes: tuple[str, ...]) -> None:
    scopes = set(envelope.scopes)
    if not any(req in scopes for req in required_scopes):
        raise PermissionError(f"Permission denied: Missing required scope from {required_scopes}")


def article_to_ref(article: NewsArticle, registry: SourceRegistryPort) -> ArticleRef:
    source_ref = registry.get_source(article.source_id)
    if not source_ref:
        source_ref = SourceRef(
            source_id=article.source_id,
            name=article.source,
            url=article.url,
            tier=min(5, max(1, article.source_tier)),
            region=article.region,
            category=article.category,
            license_class="attribution_required",
            attribution_text=f"Nguồn: {article.source}",
        )

    clean_headline = sanitize_article_content(article.headline)
    clean_summary = sanitize_article_content(article.summary)
    lang: Literal["vi", "en"] = "vi" if article.language == "vi" else "en"

    return ArticleRef(
        schema_version="1.0.0",
        article_id=article.article_id,
        headline=clean_headline,
        summary=clean_summary,
        source=source_ref,
        published_at=article.published_at,
        fetched_at=article.fetched_at,
        sort_ts=article.sort_ts,
        language=lang,
        tickers=tuple(article.tickers),
        content_hash=article.content_hash or hashlib.sha256(f"{clean_headline}|{article.url}".encode("utf-8")).hexdigest()[:32],
        is_untrusted_content=True,
    )


def load_db_articles() -> list[NewsArticle]:
    articles: list[NewsArticle] = []
    try:
        with open_app_state_db() as conn:
            rows = conn.execute(
                "SELECT * FROM news_articles ORDER BY importance_score DESC, sort_ts DESC LIMIT 100"
            ).fetchall()
            for r in rows:
                raw = dict(r)
                bd = json.loads(raw.get("importance_breakdown_json") or "{}")
                tickers = json.loads(raw.get("tickers_json") or "[]")
                aff_m = json.loads(raw.get("affected_markets_json") or "[]")
                aff_s = json.loads(raw.get("affected_sectors_json") or "[]")
                wtm = json.loads(raw.get("what_to_monitor_json") or "[]")
                ll = json.loads(raw.get("learn_links_json") or "[]")
                re_ent = json.loads(raw.get("related_entities_json") or "[]")
                articles.append(
                    NewsArticle(
                        article_id=raw["article_id"],
                        headline=raw["headline"],
                        summary=raw["summary"],
                        source=raw["source"],
                        source_id=raw["source_id"],
                        source_tier=raw["source_tier"],
                        source_flag=raw.get("source_flag", "VN"),
                        region=raw["region"],
                        category=raw["category"],
                        url=raw["url"],
                        published_at=raw["published_at"],
                        fetched_at=raw["fetched_at"],
                        sort_ts=raw["sort_ts"],
                        priority=raw.get("priority", 3),
                        sentiment=raw.get("sentiment", "neutral"),
                        impact=raw.get("impact", "medium"),
                        tickers=tickers,
                        language=raw.get("language", "vi"),
                        threat_level=raw.get("threat_level", "normal"),
                        threat_category=raw.get("threat_category"),
                        threat_confidence=float(raw.get("threat_confidence") or 0.0),
                        importance_score=raw.get("importance_score", 0),
                        importance_label=raw.get("importance_label", "noise"),
                        importance_breakdown=bd,
                        affected_markets=aff_m,
                        affected_sectors=aff_s,
                        what_to_monitor=wtm,
                        learn_links=ll,
                        related_entities=re_ent,
                    )
                )
    except Exception as exc:
        logger.warning(f"Could not load articles from app_state_db: {exc}")
    return articles
