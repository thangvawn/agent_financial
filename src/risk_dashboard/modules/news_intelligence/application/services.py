from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from risk_dashboard.modules.news_intelligence.application.clustering import cluster_articles
from risk_dashboard.modules.news_intelligence.application.rss_producer import DEFAULT_NEWS_SOURCES, NewsRssProducer
from risk_dashboard.modules.news_intelligence.domain.entities import NewsArticle, utc_now_iso
from risk_dashboard.modules.news_intelligence.safety.news_policy import build_data_quality_block, build_safety_block
from risk_dashboard.platform.database import open_app_state_db


NEWS_CACHE_TTL_SECONDS = 600
NEWS_PRESETS: dict[str, dict[str, str]] = {
    "balanced": {},
    "vietnam": {"region": "VN"},
    "us": {"region": "US"},
    "global_macro": {"source_group": "global_macro"},
    "energy": {"source_group": "commodities_energy"},
    "crypto": {"source_group": "crypto"},
}
SOURCE_BY_ID = {source.source_id: source for source in DEFAULT_NEWS_SOURCES}


class NewsIntelligenceService:
    def __init__(self, producer: NewsRssProducer | None = None) -> None:
        self.producer = producer or NewsRssProducer()

    def get_feed(
        self,
        *,
        category: str | None = None,
        query: str | None = None,
        limit: int = 50,
        time_range_hours: int = 24,
        region: str | None = None,
        source_group: str | None = None,
        preset: str | None = None,
        force: bool = False,
        sentiment: str | None = None,
        impact_level: str | None = None,
        importance: str | None = None,
    ) -> dict[str, Any]:
        selected_filters = _resolve_filters(region=region, source_group=source_group, preset=preset)
        with open_app_state_db() as conn:
            if force or self._needs_refresh(conn):
                self._refresh(conn)
            articles = self._list_articles(
                conn,
                category=category,
                query=query,
                limit=max(limit, 80),
                time_range_hours=time_range_hours,
                region=selected_filters["region"],
                source_group=selected_filters["source_group"],
                sentiment=sentiment,
                impact_level=impact_level,
                importance=importance,
            )
            latest_run = self._latest_run(conn)

        freshness = _freshness(latest_run)
        source_count = int(latest_run.get("source_count") or 0) if latest_run else 0
        successful_source_count = int(latest_run.get("successful_source_count") or 0) if latest_run else 0

        clusters = cluster_articles(articles, limit=20)
        today_brief = _build_today_brief(articles, clusters, limit=5)
        pulse = _pulse(articles, clusters, freshness, source_count, successful_source_count)

        return {
            "as_of": utc_now_iso(),
            "freshness": freshness,
            "confidence_label": "moderate" if articles else "limited",
            "stale_reason": None if freshness == "fresh" else "news_feed_cache_stale_or_unavailable",
            "source_count": source_count,
            "successful_source_count": successful_source_count,
            "selected_filters": selected_filters,
            "available_filters": _available_filters(),
            "articles": [_article_payload(article) for article in articles[:limit]],
            "today_brief": today_brief,
            "clusters": [cluster.to_dict() for cluster in clusters],
            "pulse": pulse,
            "data_quality": build_data_quality_block(
                freshness=freshness,
                source_count=source_count,
                successful_source_count=successful_source_count,
                stale_reason=None if freshness == "fresh" else "news_feed_cache_stale_or_unavailable",
                confidence_label="moderate" if articles else "limited",
            ),
            "safety": build_safety_block(),
        }

    def get_article_detail(self, article_id: str) -> dict[str, Any] | None:
        """Return full article detail with all sections."""
        with open_app_state_db() as conn:
            row = conn.execute("SELECT * FROM news_articles WHERE article_id = ?", (article_id,)).fetchone()
            if not row:
                return None
            article = _article_from_row(row)
            latest_run = self._latest_run(conn)
            # Find related articles (same category, recent)
            # Related: same category, last 24h — newest first (align with main feed ordering)
            related_rows = conn.execute(
                """
                SELECT * FROM news_articles
                WHERE category = ? AND article_id != ? AND sort_ts >= ?
                ORDER BY importance_score DESC, sort_ts DESC, fetched_at DESC, article_id ASC
                LIMIT 5
                """,
                (article.category, article_id, article.sort_ts - 86400),
            ).fetchall()
            related_articles = [_article_payload(_article_from_row(r)) for r in related_rows]

        freshness = _freshness(latest_run)
        source_count = int(latest_run.get("source_count") or 0) if latest_run else 0
        successful_source_count = int(latest_run.get("successful_source_count") or 0) if latest_run else 0
        payload = _article_payload(article)

        return {
            "article": payload,
            "badges": {
                "source_flag": article.source_flag,
                "source_tier": article.source_tier,
                "importance": article.importance_label,
                "impact_level": article.impact,
                "freshness": freshness,
                "threat_level": article.threat_level,
                "confidence": "moderate" if article.importance_score >= 50 else "limited",
            },
            "info_grid": {
                "source": article.source,
                "source_tier": f"Tier {article.source_tier}",
                "published_at": article.published_at,
                "category": article.category,
                "region": article.region,
                "source_mix": payload.get("source_group", ""),
                "tickers": article.tickers,
                "related_entities": article.related_entities,
            },
            "why_this_matters": _build_why_this_matters(article),
            "affected_markets": article.affected_markets,
            "what_to_monitor": article.what_to_monitor,
            "learn_links": article.learn_links,
            "related_articles": related_articles,
            "original_source": article.url,
            "data_quality": build_data_quality_block(
                freshness=freshness,
                source_count=source_count,
                successful_source_count=successful_source_count,
            ),
            "safety": build_safety_block(),
        }

    def save_article(self, *, user_id: str, article_id: str, note: str = "") -> None:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO saved_news (user_id, article_id, note, saved_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, article_id) DO UPDATE SET note=excluded.note, saved_at=excluded.saved_at
                """,
                (user_id, article_id, note, utc_now_iso()),
            )

    def unsave_article(self, *, user_id: str, article_id: str) -> None:
        with open_app_state_db() as conn:
            conn.execute("DELETE FROM saved_news WHERE user_id = ? AND article_id = ?", (user_id, article_id))

    def get_saved_articles(self, *, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        with open_app_state_db() as conn:
            rows = conn.execute(
                """
                SELECT s.article_id, s.note, s.saved_at, a.*
                FROM saved_news s
                LEFT JOIN news_articles a ON s.article_id = a.article_id
                WHERE s.user_id = ?
                ORDER BY s.saved_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        items: list[dict[str, Any]] = []
        for row in rows:
            row_dict = dict(row)
            if row_dict.get("headline"):
                article = _article_from_row(row)
                payload = _article_payload(article)
                payload["saved_at"] = row_dict["saved_at"]
                payload["note"] = row_dict["note"]
                items.append(payload)
            else:
                items.append({
                    "article_id": row_dict["article_id"],
                    "note": row_dict["note"],
                    "saved_at": row_dict["saved_at"],
                    "headline": "(Article no longer in cache)",
                })
        return items

    def get_source_health(self) -> list[dict[str, Any]]:
        with open_app_state_db() as conn:
            rows = conn.execute("SELECT * FROM source_health ORDER BY source_id").fetchall()
        return [dict(row) for row in rows]

    def refresh(self) -> dict[str, Any]:
        with open_app_state_db() as conn:
            self._refresh(conn)
        return self.get_feed(force=False)

    def _needs_refresh(self, conn: sqlite3.Connection) -> bool:
        latest = self._latest_run(conn)
        if not latest:
            return True
        completed_at = str(latest["completed_at"])
        try:
            age = datetime.now(timezone.utc) - datetime.fromisoformat(completed_at)
        except ValueError:
            return True
        return age.total_seconds() > NEWS_CACHE_TTL_SECONDS

    def _refresh(self, conn: sqlite3.Connection) -> None:
        started_at = utc_now_iso()
        articles, meta = self.producer.fetch()
        for article in articles:
            self._upsert_article(conn, article)

        now = utc_now_iso()
        conn.execute(
            """
            INSERT INTO news_fetch_runs (
              run_id, started_at, completed_at, source_count, successful_source_count,
              article_count, error_count, errors_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"news_run_{int(datetime.now(timezone.utc).timestamp() * 1000)}",
                started_at,
                now,
                int(meta.get("source_count") or 0),
                int(meta.get("successful_source_count") or 0),
                len(articles),
                len(meta.get("errors") or []),
                json.dumps(meta.get("errors") or [], ensure_ascii=False),
            ),
        )

        # Update source health records
        error_source_ids = {e["source_id"] for e in (meta.get("errors") or []) if "source_id" in e}
        for source in DEFAULT_NEWS_SOURCES:
            if source.source_id in error_source_ids:
                conn.execute(
                    """
                    INSERT INTO source_health (source_id, last_failure_at, failure_count, status, message)
                    VALUES (?, ?, 1, 'degraded', 'Fetch failed')
                    ON CONFLICT(source_id) DO UPDATE SET
                      last_failure_at=excluded.last_failure_at,
                      failure_count=failure_count + 1,
                      status=CASE WHEN failure_count + 1 >= 3 THEN 'degraded' ELSE 'partial' END,
                      message='Fetch failed'
                    """,
                    (source.source_id, now),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO source_health (source_id, last_success_at, failure_count, status, message)
                    VALUES (?, ?, 0, 'healthy', NULL)
                    ON CONFLICT(source_id) DO UPDATE SET
                      last_success_at=excluded.last_success_at,
                      failure_count=0,
                      status='healthy',
                      message=NULL
                    """,
                    (source.source_id, now),
                )

    def _upsert_article(self, conn: sqlite3.Connection, article: NewsArticle) -> None:
        conn.execute(
            """
            INSERT INTO news_articles (
              article_id, headline, summary, source, source_id, source_tier, source_flag,
              region, category, url, published_at, fetched_at, sort_ts, priority,
              sentiment, impact, tickers_json, language, threat_level, threat_category,
              threat_confidence,
              importance_score, importance_label, importance_breakdown_json,
              source_mix, content_hash,
              affected_markets_json, affected_sectors_json,
              what_to_monitor_json, learn_links_json, related_entities_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                      ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(article_id) DO UPDATE SET
              headline=excluded.headline,
              summary=excluded.summary,
              source=excluded.source,
              source_tier=excluded.source_tier,
              source_flag=excluded.source_flag,
              region=excluded.region,
              category=excluded.category,
              published_at=excluded.published_at,
              fetched_at=excluded.fetched_at,
              sort_ts=excluded.sort_ts,
              priority=excluded.priority,
              sentiment=excluded.sentiment,
              impact=excluded.impact,
              tickers_json=excluded.tickers_json,
              language=excluded.language,
              threat_level=excluded.threat_level,
              threat_category=excluded.threat_category,
              threat_confidence=excluded.threat_confidence,
              importance_score=excluded.importance_score,
              importance_label=excluded.importance_label,
              importance_breakdown_json=excluded.importance_breakdown_json,
              source_mix=excluded.source_mix,
              content_hash=excluded.content_hash,
              affected_markets_json=excluded.affected_markets_json,
              affected_sectors_json=excluded.affected_sectors_json,
              what_to_monitor_json=excluded.what_to_monitor_json,
              learn_links_json=excluded.learn_links_json,
              related_entities_json=excluded.related_entities_json
            """,
            (
                article.article_id,
                article.headline,
                article.summary,
                article.source,
                article.source_id,
                article.source_tier,
                article.source_flag,
                article.region,
                article.category,
                article.url,
                article.published_at,
                article.fetched_at,
                article.sort_ts,
                article.priority,
                article.sentiment,
                article.impact,
                json.dumps(article.tickers, ensure_ascii=False),
                article.language,
                article.threat_level,
                article.threat_category,
                article.threat_confidence,
                article.importance_score,
                article.importance_label,
                json.dumps(article.importance_breakdown, ensure_ascii=False),
                article.source_mix,
                article.content_hash,
                json.dumps(article.affected_markets, ensure_ascii=False),
                json.dumps(article.affected_sectors, ensure_ascii=False),
                json.dumps(article.what_to_monitor, ensure_ascii=False),
                json.dumps(article.learn_links, ensure_ascii=False),
                json.dumps(article.related_entities, ensure_ascii=False),
            ),
        )

    def _list_articles(
        self,
        conn: sqlite3.Connection,
        *,
        category: str | None,
        query: str | None,
        limit: int,
        time_range_hours: int,
        region: str | None,
        source_group: str | None,
        sentiment: str | None = None,
        impact_level: str | None = None,
        importance: str | None = None,
    ) -> list[NewsArticle]:
        since_ts = int((datetime.now(timezone.utc) - timedelta(hours=max(1, time_range_hours))).timestamp())
        where = ["sort_ts >= ?"]
        params: list[Any] = [since_ts]
        if region and region.lower() != "all":
            where.append("region = ?")
            params.append(region.upper() if region.lower() != "global" else "global")
        source_ids = _source_ids_for_group(source_group)
        if source_ids:
            placeholders = ", ".join("?" for _ in source_ids)
            where.append(f"source_id IN ({placeholders})")
            params.extend(source_ids)
        if category and category.lower() != "all":
            where.append("category = ?")
            params.append(category.lower())
        if sentiment and sentiment.lower() != "all":
            where.append("sentiment = ?")
            params.append(sentiment.lower())
        if impact_level and impact_level.lower() != "all":
            where.append("impact = ?")
            params.append(impact_level.lower())
        if importance and importance.lower() != "all":
            where.append("importance_label = ?")
            params.append(importance.lower())
        if query:
            where.append("(headline LIKE ? OR summary LIKE ? OR source LIKE ?)")
            needle = f"%{query.strip()}%"
            params.extend([needle, needle, needle])
        params.append(limit)
        # Main feed ranks important items first; recency/source tie-breakers keep ordering deterministic.
        rows = conn.execute(
            f"""
            SELECT * FROM news_articles
            WHERE {' AND '.join(where)}
            ORDER BY importance_score DESC, sort_ts DESC, fetched_at DESC, article_id ASC
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [_article_from_row(row) for row in rows]

    def _latest_run(self, conn: sqlite3.Connection) -> dict[str, Any] | None:
        row = conn.execute(
            """
            SELECT * FROM news_fetch_runs
            ORDER BY completed_at DESC
            LIMIT 1
            """
        ).fetchone()
        return dict(row) if row else None


def _article_from_row(row: sqlite3.Row) -> NewsArticle:
    return NewsArticle(
        article_id=row["article_id"],
        headline=row["headline"],
        summary=row["summary"],
        source=row["source"],
        source_id=row["source_id"],
        source_tier=int(row["source_tier"]),
        source_flag=row["source_flag"],
        region=row["region"],
        category=row["category"],
        url=row["url"],
        published_at=row["published_at"],
        fetched_at=row["fetched_at"],
        sort_ts=int(row["sort_ts"]),
        priority=int(row["priority"]),
        sentiment=row["sentiment"],
        impact=row["impact"],
        tickers=json.loads(row["tickers_json"] or "[]"),
        language=row["language"],
        threat_level=row["threat_level"],
        threat_category=row["threat_category"],
        threat_confidence=float(row["threat_confidence"] or 0),
        importance_score=int(row["importance_score"] or 0) if "importance_score" in row.keys() else 0,
        importance_label=row["importance_label"] if "importance_label" in row.keys() else "noise",
        importance_breakdown=json.loads(row["importance_breakdown_json"] or "{}") if "importance_breakdown_json" in row.keys() else {},
        source_mix=row["source_mix"] if "source_mix" in row.keys() else "",
        content_hash=row["content_hash"] if "content_hash" in row.keys() else "",
        affected_markets=json.loads(row["affected_markets_json"] or "[]") if "affected_markets_json" in row.keys() else [],
        affected_sectors=json.loads(row["affected_sectors_json"] or "[]") if "affected_sectors_json" in row.keys() else [],
        what_to_monitor=json.loads(row["what_to_monitor_json"] or "[]") if "what_to_monitor_json" in row.keys() else [],
        learn_links=json.loads(row["learn_links_json"] or "[]") if "learn_links_json" in row.keys() else [],
        related_entities=json.loads(row["related_entities_json"] or "[]") if "related_entities_json" in row.keys() else [],
    )


def _freshness(latest_run: dict[str, Any] | None) -> str:
    if not latest_run:
        return "degraded"
    try:
        age = datetime.now(timezone.utc) - datetime.fromisoformat(str(latest_run["completed_at"]))
    except ValueError:
        return "degraded"
    return "fresh" if age.total_seconds() <= NEWS_CACHE_TTL_SECONDS else "stale"


def _resolve_filters(*, region: str | None, source_group: str | None, preset: str | None) -> dict[str, str]:
    selected_preset = (preset or "balanced").strip().lower()
    preset_filters = NEWS_PRESETS.get(selected_preset, {})
    resolved_region = (region or preset_filters.get("region") or "").strip()
    resolved_group = (source_group or preset_filters.get("source_group") or "").strip()
    return {
        "preset": selected_preset if selected_preset in NEWS_PRESETS else "balanced",
        "region": resolved_region,
        "source_group": resolved_group,
    }


def _source_ids_for_group(source_group: str | None) -> list[str]:
    group = (source_group or "").strip().lower()
    if not group or group == "all":
        return []
    if group == "official":
        return [source.source_id for source in DEFAULT_NEWS_SOURCES if source.flag == "official"]
    return [source.source_id for source in DEFAULT_NEWS_SOURCES if source.source_group == group]


def _available_filters() -> dict[str, Any]:
    source_groups = sorted({source.source_group for source in DEFAULT_NEWS_SOURCES})
    regions = sorted({source.region for source in DEFAULT_NEWS_SOURCES})
    return {
        "presets": sorted(NEWS_PRESETS),
        "regions": regions,
        "source_groups": ["official", *source_groups],
        "categories": ["all", "macro", "markets", "commodities", "crypto", "regulation", "geopolitics", "technology", "earnings", "personal_finance", "risk_alerts"],
        "sentiments": ["all", "positive", "negative", "neutral"],
        "impact_levels": ["all", "high", "medium", "low"],
        "importance_labels": ["all", "critical", "high", "medium", "low", "noise"],
    }


def _article_payload(article: NewsArticle) -> dict[str, Any]:
    payload = article.to_dict()
    source = SOURCE_BY_ID.get(article.source_id)
    payload["source_group"] = source.source_group if source else "global"
    return payload


# ── Today Brief ─────────────────────────────────────────────────────────

def _build_today_brief(
    articles: list[NewsArticle],
    clusters: list,
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Select top articles by importance, deduplicate by cluster, diversify by category."""
    if not articles:
        return []

    # Sort by importance score descending
    ranked = sorted(articles, key=lambda a: a.importance_score, reverse=True)

    # Track categories used for diversity
    seen_categories: dict[str, int] = {}
    seen_headlines: set[str] = set()
    brief: list[dict[str, Any]] = []

    for article in ranked:
        if len(brief) >= limit:
            break
        # Skip if category already has 2 entries (diversity)
        cat_count = seen_categories.get(article.category, 0)
        if cat_count >= 2:
            continue
        # Skip very similar headlines (simple dedup)
        headline_key = article.headline[:60].lower()
        if headline_key in seen_headlines:
            continue
        seen_headlines.add(headline_key)
        seen_categories[article.category] = cat_count + 1

        brief.append({
            "article_id": article.article_id,
            "headline": article.headline,
            "source": article.source,
            "published_at": article.published_at,
            "time": article.published_at[11:16] if "T" in article.published_at else "",
            "importance_score": article.importance_score,
            "importance_label": article.importance_label,
            "category": article.category,
            "region": article.region,
            "sentiment": article.sentiment,
            "impact": article.impact,
            "why_it_matters": _brief_why(article),
            "affected_markets": article.affected_markets[:3],
            "source_flag": article.source_flag,
        })

    return brief


def _brief_why(article: NewsArticle) -> str:
    """Generate a one-line why-it-matters for Today Brief card."""
    parts = []
    if article.importance_label in ("critical", "high"):
        parts.append(f"Tin {article.importance_label} impact")
    if article.affected_markets:
        parts.append(f"ảnh hưởng {', '.join(article.affected_markets[:2])}")
    if article.threat_level != "normal":
        parts.append(f"risk: {article.threat_level}")
    if not parts:
        parts.append(f"Phân loại: {article.category} · {article.sentiment}")
    return " — ".join(parts) + "."


# ── Enhanced Pulse ──────────────────────────────────────────────────────

def _pulse(
    articles: list[NewsArticle],
    clusters: list,
    freshness: str,
    source_count: int,
    successful_source_count: int,
) -> dict[str, Any]:
    return {
        "article_count": len(articles),
        "high_impact_count": sum(1 for article in articles if article.impact == "high"),
        "negative_count": sum(1 for article in articles if article.sentiment == "negative"),
        "positive_count": sum(1 for article in articles if article.sentiment == "positive"),
        "critical_count": sum(1 for article in articles if article.importance_label == "critical"),
        "top_categories": _top_counts(article.category for article in articles),
        "top_sources": _top_counts(article.source for article in articles),
        "top_regions": _top_counts(article.region for article in articles),
        "risk_labels": sorted({article.threat_level for article in articles if article.threat_level != "normal"}),
        # ── New fields ──
        "top_drivers": _top_drivers(articles),
        "top_affected_markets": _top_counts(
            market for article in articles for market in article.affected_markets
        ),
        "source_health": {
            "total": source_count,
            "active": successful_source_count,
            "status": "healthy" if successful_source_count >= source_count * 0.8 else ("partial" if successful_source_count >= source_count * 0.5 else "degraded"),
        },
        "freshness_status": freshness,
        "cluster_count": len(clusters),
        "cluster_summary": [
            {
                "cluster_id": cluster.cluster_id,
                "topic": cluster.similarity_topic,
                "article_count": len(cluster.articles),
                "sentiment": cluster.lead_article.sentiment,
                "importance": cluster.lead_article.importance_label,
            }
            for cluster in clusters[:5]
        ],
    }


def _top_drivers(articles: list[NewsArticle]) -> list[dict[str, Any]]:
    """Extract top-driving topics from articles."""
    keyword_counts: dict[str, int] = {}
    driver_keywords = {"fed", "inflation", "oil", "gold", "bitcoin", "rate", "tariff", "earnings", "war", "china", "ecb", "recession", "usd", "vn-index", "crypto"}
    for article in articles:
        text = f"{article.headline} {article.summary}".lower()
        for kw in driver_keywords:
            if kw in text:
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
    sorted_drivers = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
    return [{"label": kw, "count": count} for kw, count in sorted_drivers[:6]]


def _top_counts(values) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return [{"label": key, "count": value} for key, value in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:5]]


# ── Why This Matters ────────────────────────────────────────────────────

def _build_why_this_matters(article: NewsArticle) -> str:
    """Generate contextual explanation for article detail."""
    parts = [
        "Tin được phân loại theo source tier, sentiment, impact và risk keywords.",
        "Đây là lớp đọc bối cảnh, không phải tín hiệu mua bán hay khuyến nghị đầu tư cá nhân hóa.",
    ]
    if article.importance_label in ("critical", "high"):
        parts.insert(0, f"Đây là tin {article.importance_label} importance (score: {article.importance_score}/100).")
    if article.affected_markets:
        parts.append(f"Tin này có thể liên quan đến: {', '.join(article.affected_markets)}.")
    if article.threat_level != "normal":
        parts.append(f"Mức cảnh báo: {article.threat_level}.")
    return " ".join(parts)
