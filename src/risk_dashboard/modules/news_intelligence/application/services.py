from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from risk_dashboard.modules.news_intelligence.application.clustering import cluster_articles
from risk_dashboard.modules.news_intelligence.application.rss_producer import DEFAULT_NEWS_SOURCES, NewsRssProducer
from risk_dashboard.modules.news_intelligence.domain.entities import NewsArticle, utc_now_iso
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
            )
            latest_run = self._latest_run(conn)

        freshness = _freshness(latest_run)
        clusters = cluster_articles(articles, limit=20)
        return {
            "as_of": utc_now_iso(),
            "freshness": freshness,
            "confidence_label": "moderate" if articles else "limited",
            "stale_reason": None if freshness == "fresh" else "news_feed_cache_stale_or_unavailable",
            "source_count": int(latest_run.get("source_count") or 0) if latest_run else 0,
            "successful_source_count": int(latest_run.get("successful_source_count") or 0) if latest_run else 0,
            "selected_filters": selected_filters,
            "available_filters": _available_filters(),
            "articles": [_article_payload(article) for article in articles[:limit]],
            "clusters": [cluster.to_dict() for cluster in clusters],
            "pulse": _pulse(articles),
        }

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
                utc_now_iso(),
                int(meta.get("source_count") or 0),
                int(meta.get("successful_source_count") or 0),
                len(articles),
                len(meta.get("errors") or []),
                json.dumps(meta.get("errors") or [], ensure_ascii=False),
            ),
        )

    def _upsert_article(self, conn: sqlite3.Connection, article: NewsArticle) -> None:
        conn.execute(
            """
            INSERT INTO news_articles (
              article_id, headline, summary, source, source_id, source_tier, source_flag,
              region, category, url, published_at, fetched_at, sort_ts, priority,
              sentiment, impact, tickers_json, language, threat_level, threat_category,
              threat_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
              threat_confidence=excluded.threat_confidence
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
        if query:
            where.append("(headline LIKE ? OR summary LIKE ? OR source LIKE ?)")
            needle = f"%{query.strip()}%"
            params.extend([needle, needle, needle])
        params.append(limit)
        rows = conn.execute(
            f"""
            SELECT * FROM news_articles
            WHERE {' AND '.join(where)}
            ORDER BY sort_ts DESC, priority DESC, source_tier ASC
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
    }


def _article_payload(article: NewsArticle) -> dict[str, Any]:
    payload = article.to_dict()
    source = SOURCE_BY_ID.get(article.source_id)
    payload["source_group"] = source.source_group if source else "global"
    return payload


def _pulse(articles: list[NewsArticle]) -> dict[str, Any]:
    return {
        "article_count": len(articles),
        "high_impact_count": sum(1 for article in articles if article.impact == "high"),
        "negative_count": sum(1 for article in articles if article.sentiment == "negative"),
        "positive_count": sum(1 for article in articles if article.sentiment == "positive"),
        "top_categories": _top_counts(article.category for article in articles),
        "top_sources": _top_counts(article.source for article in articles),
        "top_regions": _top_counts(article.region for article in articles),
        "risk_labels": sorted({article.threat_level for article in articles if article.threat_level != "normal"}),
    }


def _top_counts(values) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return [{"label": key, "count": value} for key, value in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:5]]
