from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from risk_dashboard.modules.news_intelligence.application.clustering import cluster_articles
from risk_dashboard.modules.news_intelligence.application.highlights import (
    get_or_build_snapshot,
    rebuild_current_snapshots,
)
from risk_dashboard.modules.news_intelligence.application.rss_producer import (
    DEFAULT_NEWS_SOURCES,
    NewsRssProducer,
)
from risk_dashboard.modules.news_intelligence.domain.entities import NewsArticle, utc_now_iso
from risk_dashboard.modules.news_intelligence.domain.scoring import calculate_importance
from risk_dashboard.modules.news_intelligence.domain.text import contains_keyword, normalize_text
from risk_dashboard.modules.news_intelligence.domain.time import parse_utc_datetime
from risk_dashboard.modules.news_intelligence.safety.news_policy import (
    build_data_quality_block,
    build_safety_block,
)
from risk_dashboard.platform.database import open_app_state_db

# RSS sources are polled frequently enough for the News surface to feel live,
# while the persisted cache still prevents every browser request from fanning
# out into a full source refresh.  The frontend polls more frequently than this
# value; only the first request after the TTL performs the refresh.
try:
    NEWS_CACHE_TTL_SECONDS = max(15, int(os.getenv("NEWS_CACHE_TTL_SECONDS", "60")))
except ValueError:
    NEWS_CACHE_TTL_SECONDS = 60
NEWS_PRESETS: dict[str, dict[str, str]] = {
    "balanced": {},
    "vietnam": {"region": "VN"},
    "us": {"region": "US"},
    "global_macro": {"source_group": "global_macro"},
    "energy": {"source_group": "commodities_energy"},
    "crypto": {"source_group": "crypto"},
}
SOURCE_BY_ID = {source.source_id: source for source in DEFAULT_NEWS_SOURCES}
logger = logging.getLogger(__name__)


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
        refresh_failed = False
        importance_filter = (
            importance.strip().lower()
            if importance and importance.strip().lower() != "all"
            else ""
        )
        has_scoped_view = any(
            (
                category and category.strip().lower() != "all",
                (query or "").strip(),
                selected_filters["region"],
                selected_filters["source_group"],
                sentiment and sentiment.strip().lower() != "all",
                impact_level and impact_level.strip().lower() != "all",
                importance_filter,
            )
        )
        with open_app_state_db() as conn:
            if force or self._needs_refresh(conn):
                conn.execute("SAVEPOINT news_feed_refresh")
                try:
                    self._refresh(conn)
                except Exception:  # noqa: BLE001 - stale cache is safer than a blank dashboard.
                    conn.execute("ROLLBACK TO SAVEPOINT news_feed_refresh")
                    conn.execute("RELEASE SAVEPOINT news_feed_refresh")
                    refresh_failed = True
                    logger.exception("News refresh failed; serving the last persisted feed")
                else:
                    conn.execute("RELEASE SAVEPOINT news_feed_refresh")
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
                # Re-score before applying the importance filter so a score
                # change caused by cluster breadth cannot leak an article into
                # the wrong label.
                importance=None if importance_filter else importance,
            )
            latest_run = self._latest_run(conn)
            clusters = cluster_articles(articles, limit=20)
            if _apply_cluster_scores(conn, articles, clusters, persist=not has_scoped_view):
                articles.sort(key=_article_rank_key)
                clusters = cluster_articles(articles, limit=20)
                if latest_run and not has_scoped_view:
                    rebuild_current_snapshots(conn, source_run_id=latest_run.get("run_id"))
            if importance_filter:
                articles = [article for article in articles if article.importance_label == importance_filter]
                clusters = cluster_articles(articles, limit=20)

        freshness = _freshness(latest_run)
        source_count = int(latest_run.get("source_count") or 0) if latest_run else 0
        successful_source_count = int(latest_run.get("successful_source_count") or 0) if latest_run else 0
        http_cache = {
            "conditional_request_count": int(latest_run.get("conditional_request_count") or 0) if latest_run else 0,
            "not_modified_count": int(latest_run.get("not_modified_count") or 0) if latest_run else 0,
        }

        today_brief = _build_today_brief(articles, clusters, limit=5)
        pulse = _pulse(articles, clusters, freshness, source_count, successful_source_count)
        stale_reason = _stale_reason(
            freshness,
            refresh_failed=refresh_failed,
            has_cache=bool(articles),
        )

        return {
            "as_of": utc_now_iso(),
            "freshness": freshness,
            "confidence_label": "moderate" if articles else "limited",
            "stale_reason": stale_reason,
            "source_count": source_count,
            "successful_source_count": successful_source_count,
            "http_cache": http_cache,
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
                stale_reason=stale_reason,
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
            if not conn.execute(
                "SELECT 1 FROM news_articles WHERE article_id = ?", (article_id,)
            ).fetchone():
                raise ValueError("Article not found")
            conn.execute(
                """
                INSERT INTO saved_news (user_id, article_id, note, saved_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, article_id) DO UPDATE SET note=excluded.note, saved_at=excluded.saved_at
                """,
                (user_id, article_id, note, utc_now_iso()),
            )

    def get_highlights(
        self,
        *,
        period: str = "day",
        limit: int = 5,
        force: bool = False,
    ) -> dict[str, Any]:
        refresh_failed = False
        with open_app_state_db() as conn:
            if force or self._needs_refresh(conn):
                conn.execute("SAVEPOINT news_highlight_refresh")
                try:
                    self._refresh(conn)
                except Exception:
                    conn.execute("ROLLBACK TO SAVEPOINT news_highlight_refresh")
                    conn.execute("RELEASE SAVEPOINT news_highlight_refresh")
                    refresh_failed = True
                    logger.exception("News refresh failed; serving persisted highlights")
                else:
                    conn.execute("RELEASE SAVEPOINT news_highlight_refresh")
            snapshot = get_or_build_snapshot(conn, period)
            latest_run = self._latest_run(conn)

        freshness = _freshness(latest_run)
        source_count = int(latest_run.get("source_count") or 0) if latest_run else 0
        successful_source_count = (
            int(latest_run.get("successful_source_count") or 0) if latest_run else 0
        )
        items = snapshot["items"][:limit]
        return {
            "period": snapshot["period_kind"],
            "period_key": snapshot["period_key"],
            "timezone": snapshot["timezone"],
            "window_start": snapshot["window_start"],
            "window_end": snapshot["window_end"],
            "as_of": utc_now_iso(),
            "requested_limit": limit,
            "count": len(items),
            "items": items,
            "generated_at": snapshot["generated_at"],
            "freshness": freshness,
            "data_quality": build_data_quality_block(
                freshness=freshness,
                source_count=source_count,
                successful_source_count=successful_source_count,
                stale_reason=(
                    "news_refresh_failed_using_persisted_snapshot"
                    if refresh_failed
                    else None if freshness == "fresh"
                    else "news_feed_cache_stale_or_unavailable"
                ),
                confidence_label="moderate" if items else "limited",
            ),
            "safety": build_safety_block(),
        }

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
        return self.get_feed(force=True)

    def _needs_refresh(self, conn: sqlite3.Connection) -> bool:
        latest = self._latest_run(conn)
        if not latest:
            return True
        completed_at = parse_utc_datetime(latest.get("completed_at"))
        if completed_at is None:
            return True
        age_seconds = max(0.0, (datetime.now(timezone.utc) - completed_at).total_seconds())
        return age_seconds > NEWS_CACHE_TTL_SECONDS

    def _refresh(self, conn: sqlite3.Connection) -> None:
        started_at = utc_now_iso()
        articles, meta = self.producer.fetch()
        for article in articles:
            self._upsert_article(conn, article)

        now = utc_now_iso()
        run_id = f"news_run_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        conn.execute(
            """
            INSERT INTO news_fetch_runs (
              run_id, started_at, completed_at, source_count, successful_source_count,
              article_count, error_count, errors_json, conditional_request_count,
              not_modified_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                started_at,
                now,
                int(meta.get("source_count") or 0),
                int(meta.get("successful_source_count") or 0),
                len(articles),
                len(meta.get("errors") or []),
                json.dumps(meta.get("errors") or [], ensure_ascii=False),
                int(meta.get("conditional_request_source_count") or 0),
                int(meta.get("not_modified_source_count") or 0),
            ),
        )

        # Update the actual producer catalogue.  This matters for tests,
        # deployments with a regional feed set, and future custom providers.
        error_source_ids = {e["source_id"] for e in (meta.get("errors") or []) if "source_id" in e}
        configured_sources = tuple(getattr(self.producer, "sources", ()) or ())
        source_catalog = configured_sources or DEFAULT_NEWS_SOURCES
        source_ids = set(meta.get("source_ids") or ())
        if source_ids:
            source_catalog = tuple(source for source in source_catalog if source.source_id in source_ids)
        for source in source_catalog:
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

        rebuild_current_snapshots(conn, source_run_id=run_id)

    def _upsert_article(self, conn: sqlite3.Connection, article: NewsArticle) -> None:
        conn.execute(
            """
            INSERT INTO news_articles (
              article_id, headline, summary, source, source_id, source_tier, source_flag,
              region, category, url, image_url, published_at, fetched_at, sort_ts, priority,
              sentiment, impact, tickers_json, language, threat_level, threat_category,
              threat_confidence,
              importance_score, importance_label, importance_breakdown_json,
              source_mix, content_hash,
              affected_markets_json, affected_sectors_json,
              what_to_monitor_json, learn_links_json, related_entities_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                      ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(article_id) DO UPDATE SET
              headline=excluded.headline,
              summary=excluded.summary,
              source=excluded.source,
              source_tier=excluded.source_tier,
              source_flag=excluded.source_flag,
              region=excluded.region,
              category=excluded.category,
              image_url=CASE WHEN excluded.image_url <> '' THEN excluded.image_url ELSE news_articles.image_url END,
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
                article.image_url,
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
        where = [
            "sort_ts >= ?",
            "headline NOT LIKE 'Distinct financial event number %'",
        ]
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
        query_text = (query or "").strip()
        if query_text:
            where.append(
                """
                (
                  headline LIKE ? OR summary LIKE ? OR source LIKE ? OR source_id LIKE ?
                  OR category LIKE ? OR region LIKE ? OR sentiment LIKE ? OR impact LIKE ?
                  OR tickers_json LIKE ? OR affected_markets_json LIKE ?
                  OR affected_sectors_json LIKE ? OR related_entities_json LIKE ?
                )
                """
            )
            needle = f"%{query_text}%"
            params.extend([needle] * 12)
        # Fetch a small overage so syndication duplicates do not consume the
        # entire requested page before deduplication.
        params.append(min(500, max(limit + 20, limit * 3)))
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
        articles = [_article_from_row(row) for row in rows]
        return _deduplicate_articles(articles)[:limit]

    def _latest_run(self, conn: sqlite3.Connection) -> dict[str, Any] | None:
        rows = conn.execute("SELECT * FROM news_fetch_runs").fetchall()
        if not rows:
            return None
        # ISO UTC strings sort lexically, but legacy rows can contain offsets
        # or naive timestamps.  Parse before choosing the newest run.
        return dict(max(rows, key=lambda row: parse_utc_datetime(row["completed_at"]) or datetime.min.replace(tzinfo=timezone.utc)))


def _article_rank_key(article: NewsArticle) -> tuple[int, int, int, str]:
    return (-article.importance_score, -article.sort_ts, article.source_tier, article.article_id)


def _headline_dedupe_key(article: NewsArticle) -> str:
    normalized = re.sub(r"[^\w]+", " ", normalize_text(article.headline)).strip()
    # Very short/generic headlines are recurring market labels rather than a
    # reliable identity, so only use a key when it carries enough information.
    if len(normalized) < 20 or len(normalized.split()) < 4:
        return ""
    return f"{article.category}:{article.sort_ts // 86400}:{normalized}"


def _deduplicate_articles(articles: list[NewsArticle]) -> list[NewsArticle]:
    """Collapse syndicated copies while preserving the best ranked source."""

    seen_hashes: set[str] = set()
    seen_headlines: set[str] = set()
    unique: list[NewsArticle] = []
    for article in articles:
        content_hash = (article.content_hash or "").strip()
        headline_key = _headline_dedupe_key(article)
        if content_hash and content_hash in seen_hashes:
            continue
        if headline_key and headline_key in seen_headlines:
            continue
        if content_hash:
            seen_hashes.add(content_hash)
        if headline_key:
            seen_headlines.add(headline_key)
        unique.append(article)
    return unique


def _apply_cluster_scores(
    conn: sqlite3.Connection,
    articles: list[NewsArticle],
    clusters: list,
    *,
    persist: bool,
) -> bool:
    """Re-score articles with observed cluster breadth, optionally persisting it."""

    now = datetime.now(timezone.utc)
    changed = False
    for cluster in clusters:
        cluster_size = len(cluster.articles)
        # A singleton already carries the producer's canonical score.  Only
        # clustered events need a context adjustment; preserving singleton
        # values also keeps custom producers' explicit classifications intact.
        if cluster_size < 2:
            continue
        for article in cluster.articles:
            published_at = parse_utc_datetime(article.published_at)
            age_minutes = 60.0 if published_at is None else max(
                0.0, (now - published_at).total_seconds() / 60
            )
            result = calculate_importance(
                headline=article.headline,
                summary=article.summary,
                source_tier=article.source_tier,
                impact=article.impact,
                sentiment=article.sentiment,
                threat_level=article.threat_level,
                age_minutes=age_minutes,
                cluster_size=cluster_size,
                is_duplicate=False,
            )
            if (
                article.importance_score == result.score
                and article.importance_label == result.label
                and article.importance_breakdown == result.breakdown.to_dict()
            ):
                continue
            article.importance_score = result.score
            article.importance_label = result.label
            article.importance_breakdown = result.breakdown.to_dict()
            if persist:
                conn.execute(
                    """
                    UPDATE news_articles
                    SET importance_score = ?, importance_label = ?, importance_breakdown_json = ?
                    WHERE article_id = ?
                    """,
                    (
                        result.score,
                        result.label,
                        json.dumps(result.breakdown.to_dict(), ensure_ascii=False),
                        article.article_id,
                    ),
                )
            changed = True
    return changed


def _safe_json(value: object, fallback: Any) -> Any:
    try:
        decoded = json.loads(value or "")
    except (TypeError, ValueError, json.JSONDecodeError):
        return fallback
    return decoded


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
        image_url=row["image_url"] if "image_url" in row.keys() else "",
        published_at=row["published_at"],
        fetched_at=row["fetched_at"],
        sort_ts=int(row["sort_ts"]),
        priority=int(row["priority"]),
        sentiment=row["sentiment"],
        impact=row["impact"],
        tickers=_safe_json(row["tickers_json"], []),
        language=row["language"],
        threat_level=row["threat_level"],
        threat_category=row["threat_category"],
        threat_confidence=float(row["threat_confidence"] or 0),
        importance_score=int(row["importance_score"] or 0) if "importance_score" in row.keys() else 0,
        importance_label=row["importance_label"] if "importance_label" in row.keys() else "noise",
        importance_breakdown=_safe_json(row["importance_breakdown_json"], {}) if "importance_breakdown_json" in row.keys() else {},
        source_mix=row["source_mix"] if "source_mix" in row.keys() else "",
        content_hash=row["content_hash"] if "content_hash" in row.keys() else "",
        affected_markets=_safe_json(row["affected_markets_json"], []) if "affected_markets_json" in row.keys() else [],
        affected_sectors=_safe_json(row["affected_sectors_json"], []) if "affected_sectors_json" in row.keys() else [],
        what_to_monitor=_safe_json(row["what_to_monitor_json"], []) if "what_to_monitor_json" in row.keys() else [],
        learn_links=_safe_json(row["learn_links_json"], []) if "learn_links_json" in row.keys() else [],
        related_entities=_safe_json(row["related_entities_json"], []) if "related_entities_json" in row.keys() else [],
    )


def _freshness(latest_run: dict[str, Any] | None) -> str:
    if not latest_run:
        return "degraded"
    completed_at = parse_utc_datetime(latest_run.get("completed_at"))
    if completed_at is None:
        return "degraded"
    age_seconds = max(0.0, (datetime.now(timezone.utc) - completed_at).total_seconds())
    source_count = int(latest_run.get("source_count") or 0)
    successful_count = int(latest_run.get("successful_source_count") or 0)
    if source_count > 0 and successful_count == 0:
        return "degraded"
    return "fresh" if age_seconds <= NEWS_CACHE_TTL_SECONDS else "stale"


def _stale_reason(
    freshness: str,
    *,
    refresh_failed: bool = False,
    has_cache: bool = True,
) -> str | None:
    if refresh_failed:
        return (
            "news_refresh_failed_using_persisted_cache"
            if has_cache
            else "news_refresh_failed_no_cache"
        )
    if freshness == "degraded":
        return "news_sources_unavailable_or_timestamp_invalid"
    if freshness == "stale":
        return "news_feed_cache_stale_or_unavailable"
    return None


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

    cluster_by_article = {
        article.article_id: cluster.cluster_id
        for cluster in clusters
        for article in cluster.articles
    }
    seen_clusters: set[str] = set()
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
        cluster_id = cluster_by_article.get(article.article_id)
        if cluster_id and cluster_id in seen_clusters:
            continue
        # Skip very similar headlines (simple dedup)
        headline_key = article.headline[:60].lower()
        if headline_key in seen_headlines:
            continue
        seen_headlines.add(headline_key)
        if cluster_id:
            seen_clusters.add(cluster_id)
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
    driver_keywords = (
        "fed", "inflation", "oil", "gold", "bitcoin", "rate", "tariff", "earnings",
        "war", "china", "ecb", "recession", "usd", "vn-index", "crypto",
        "lạm phát", "lãi suất", "tỷ giá", "ngân hàng", "chứng khoán",
    )
    for article in articles:
        text = f"{article.headline} {article.summary}"
        for kw in driver_keywords:
            if contains_keyword(text, kw):
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
    sorted_drivers = sorted(keyword_counts.items(), key=lambda item: (-item[1], item[0]))
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
