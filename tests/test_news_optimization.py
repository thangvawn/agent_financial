from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree as ET
import urllib.request

import pytest

from risk_dashboard.modules.news_intelligence.application.clustering import cluster_articles
from risk_dashboard.modules.news_intelligence.application.enrichment import enrich_article
from risk_dashboard.modules.news_intelligence.application.rss_producer import NewsRssProducer
from risk_dashboard.modules.news_intelligence.application.services import (
    NewsIntelligenceService,
    _freshness,
)
from risk_dashboard.modules.news_intelligence.domain.entities import NewsArticle, NewsSource
from risk_dashboard.modules.news_intelligence.domain.scoring import calculate_importance
from risk_dashboard.modules.news_intelligence.domain.time import parse_utc_datetime
from risk_dashboard.platform.database import (
    clear_db_path_cache,
    clear_migration_cache,
    open_app_state_db,
    reset_app_state_tables,
)


@pytest.fixture(autouse=True)
def isolated_news_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RISK_DASHBOARD_DB_PATH", str(tmp_path / "news.sqlite3"))
    clear_db_path_cache()
    clear_migration_cache()
    yield
    clear_db_path_cache()
    clear_migration_cache()


def _article(article_id: str, headline: str, *, sort_ts: int | None = None) -> NewsArticle:
    now = datetime.now(timezone.utc)
    timestamp = int(now.timestamp()) if sort_ts is None else sort_ts
    article = NewsArticle(
        article_id=article_id,
        headline=headline,
        summary="Market context for the latest financial event.",
        source="Test source",
        source_id="test_source",
        source_tier=2,
        source_flag="major_media",
        region="global",
        category="markets",
        url=f"https://example.test/{article_id}",
        published_at=datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat(),
        fetched_at=now.isoformat(),
        sort_ts=timestamp,
    )
    return enrich_article(article)


class DuplicateProducer:
    def fetch(self):
        first = _article("dup-1", "Fed signals rate patience as inflation cools")
        second = _article("dup-2", "Fed signals rate patience as inflation cools")
        second.source_id = "other_source"
        return [first, second], {
            "source_count": 2,
            "successful_source_count": 2,
            "source_ids": ["test_source", "other_source"],
            "errors": [],
        }


def test_time_parser_and_freshness_accept_legacy_timestamp_shapes():
    assert parse_utc_datetime("2026-09-27T10:00:00Z").tzinfo is timezone.utc
    assert parse_utc_datetime("2026-09-27T10:00:00") == datetime(
        2026, 9, 27, 10, tzinfo=timezone.utc
    )
    assert parse_utc_datetime("Sun, 27 Sep 2026 10:00:00 GMT").tzinfo is timezone.utc
    assert parse_utc_datetime("not-a-date") is None

    assert _freshness({
        "completed_at": "2026-09-27T10:00:00",
        "source_count": 1,
        "successful_source_count": 1,
    }) in {
        "fresh",
        "stale",
    }
    assert _freshness({"completed_at": "not-a-date"}) == "degraded"
    assert _freshness({
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "source_count": 2,
        "successful_source_count": 0,
    }) == "degraded"


def test_rss_producer_extracts_media_image_and_relative_html_image():
    producer = NewsRssProducer()
    source = NewsSource("test", "Test", "https://example.test/feed.xml", "markets", "US", 2, "media")
    root = ET.fromstring(
        """
        <rss xmlns:media="http://search.yahoo.com/mrss/"><channel>
          <item>
            <title>Media image</title>
            <link>https://example.test/story</link>
            <media:thumbnail url="https://cdn.example.test/thumb.jpg" />
          </item>
          <item>
            <title>HTML image</title>
            <link>https://example.test/story-2</link>
            <description><![CDATA[<p>Summary</p><img src="/images/story.jpg" />]]></description>
          </item>
        </channel></rss>
        """
    )
    articles = producer._parse_items(root=root, source=source, fetched_at=datetime.now(timezone.utc).isoformat())
    assert articles[0].image_url == "https://cdn.example.test/thumb.jpg"
    assert articles[1].image_url == "https://example.test/images/story.jpg"


def test_rss_producer_reuses_cached_body_after_not_modified_response(monkeypatch: pytest.MonkeyPatch):
    """The second poll sends validators and parses the cached XML after 304."""
    source = NewsSource(
        "conditional_source",
        "Conditional source",
        "https://conditional.example.test/feed.xml",
        "markets",
        "US",
        2,
        "major_media",
    )
    xml = b"""<rss><channel><item>
      <title>Conditional feed story</title>
      <link>https://conditional.example.test/story</link>
      <pubDate>Tue, 29 Sep 2026 10:00:00 GMT</pubDate>
    </item></channel></rss>"""
    calls: list[dict[str, str]] = []

    class FakeResponse:
        def __init__(self, body: bytes, *, status: int, headers: dict[str, str]):
            self._body = body
            self.status = status
            self.code = status
            self.headers = headers

        def read(self, _limit: int) -> bytes:
            return self._body

        def geturl(self) -> str:
            return source.url

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    def fake_urlopen(request, timeout):
        del timeout
        calls.append({key.lower(): value for key, value in request.header_items()})
        if len(calls) == 1:
            return FakeResponse(xml, status=200, headers={"ETag": '"feed-v1"'})
        return FakeResponse(b"", status=304, headers={"ETag": '"feed-v1"'})

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    producer = NewsRssProducer(sources=(source,))

    first_articles, first_meta = producer.fetch()
    second_articles, second_meta = producer.fetch()

    assert len(first_articles) == len(second_articles) == 1
    assert first_meta["not_modified_source_count"] == 0
    assert second_meta["not_modified_source_count"] == 1
    assert second_meta["conditional_request_source_count"] == 1
    assert calls[1]["if-none-match"] == '"feed-v1"'


def test_feed_deduplicates_same_day_syndication_and_keeps_best_ranked_copy():
    reset_app_state_tables()
    feed = NewsIntelligenceService(producer=DuplicateProducer()).get_feed(force=True)
    assert len(feed["articles"]) == 1
    assert feed["articles"][0]["article_id"] in {"dup-1", "dup-2"}
    assert feed["pulse"]["article_count"] == 1


def test_failed_refresh_serves_cache_and_exposes_reason():
    reset_app_state_tables()
    service = NewsIntelligenceService(producer=DuplicateProducer())
    service.get_feed(force=True)
    with open_app_state_db() as conn:
        conn.execute(
            "UPDATE news_fetch_runs SET completed_at = ?",
            ((datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(),),
        )

    class FailingProducer:
        def fetch(self):
            raise RuntimeError("network unavailable")

    fallback = NewsIntelligenceService(producer=FailingProducer()).get_feed(force=True)
    assert fallback["articles"]
    assert fallback["stale_reason"] == "news_refresh_failed_using_persisted_cache"
    assert fallback["freshness"] == "stale"


def test_custom_source_catalogue_updates_source_health():
    source = NewsSource(
        "custom_source",
        "Custom",
        "https://example.test/rss",
        "markets",
        "VN",
        3,
        "specialist",
        "vn_markets",
    )

    class CustomProducer:
        sources = (source,)

        def fetch(self):
            return [], {
                "source_count": 1,
                "successful_source_count": 0,
                "source_ids": [source.source_id],
                "errors": [{"source_id": source.source_id, "error": "timeout"}],
            }

    reset_app_state_tables()
    NewsIntelligenceService(producer=CustomProducer()).get_feed(force=True)
    with open_app_state_db() as conn:
        rows = conn.execute("SELECT source_id, status, failure_count FROM source_health").fetchall()
    assert [tuple(row) for row in rows] == [("custom_source", "degraded", 1)]


def test_vietnamese_clustering_is_deterministic_and_velocity_uses_time_span():
    now = int(datetime.now(timezone.utc).timestamp())
    first = _article(
        "vi-1",
        "Lãi suất ngân hàng tăng, thị trường chứng khoán biến động",
        sort_ts=now,
    )
    second = _article(
        "vi-2",
        "Lai suat ngan hang tang, thi truong chung khoan bien dong",
        sort_ts=now - 60,
    )
    clusters = cluster_articles([second, first])
    assert len(clusters) == 1
    assert clusters[0].velocity == "building"
    assert clusters[0].similarity_topic == cluster_articles([first, second])[0].similarity_topic


def test_scoring_uses_word_boundaries_for_high_impact_keywords():
    baseline = calculate_importance(
        headline="Hardware corporate update",
        summary="A routine software release.",
        source_tier=3,
        impact="low",
        sentiment="neutral",
        threat_level="normal",
        age_minutes=60,
    )
    explicit = calculate_importance(
        headline="War risk raises oil prices",
        summary="Markets assess the shock.",
        source_tier=3,
        impact="low",
        sentiment="negative",
        threat_level="watch",
        age_minutes=60,
    )
    assert explicit.score > baseline.score


def test_atom_namespace_and_tracking_url_are_parsed_canonically():
    xml = """
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>Market update</title>
        <summary>Summary</summary>
        <link rel="alternate" href="https://example.test/story/?utm_source=rss&amp;id=9#fragment" />
        <published>Sun, 27 Sep 2026 10:00:00 GMT</published>
      </entry>
    </feed>
    """
    source = NewsSource(
        "atom", "Atom", "https://example.test/feed", "markets", "US", 2, "major_media"
    )
    root = ET.fromstring(xml)
    articles = NewsRssProducer(sources=(source,))._parse_items(
        root=root, source=source, fetched_at=datetime.now(timezone.utc).isoformat()
    )
    assert articles[0].url == "https://example.test/story?id=9"
