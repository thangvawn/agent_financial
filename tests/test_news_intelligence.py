from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.news_intelligence.application.enrichment import enrich_article
from risk_dashboard.modules.news_intelligence.application.services import NewsIntelligenceService
from risk_dashboard.modules.news_intelligence.domain.entities import NewsArticle
from risk_dashboard.platform.database import reset_app_state_tables


def _article(
    article_id: str,
    headline: str,
    *,
    source_id: str = "fed_press",
    source: str = "Federal Reserve",
    region: str = "US",
    category: str = "macro",
) -> NewsArticle:
    now = datetime.now(timezone.utc)
    return enrich_article(
        NewsArticle(
            article_id=article_id,
            headline=headline,
            summary="Inflation and rate policy remain in focus for global markets.",
            source=source,
            source_id=source_id,
            source_tier=1,
            source_flag="official",
            region=region,
            category=category,
            url=f"https://example.com/{article_id}",
            published_at=now.isoformat(),
            fetched_at=now.isoformat(),
            sort_ts=int(now.timestamp()),
        )
    )


class FakeProducer:
    def fetch(self):
        return (
            [
                _article("a1", "Fed signals rate patience as markets digest inflation risk"),
                _article("a2", "Fed officials discuss inflation risk and rate outlook", source_id="bbc_business", source="BBC Business"),
                _article("a3", "Bitcoin rally lifts crypto risk appetite", source_id="coindesk", source="CoinDesk", category="crypto"),
                _article("a4", "VN stocks rise as banking liquidity improves", source_id="cafef_stock", source="CafeF Chứng khoán", region="VN", category="markets"),
            ],
            {"source_count": 4, "successful_source_count": 4, "errors": []},
        )


def test_news_intelligence_feed_enriches_and_clusters():
    reset_app_state_tables()
    feed = NewsIntelligenceService(producer=FakeProducer()).get_feed(force=True)

    assert feed["freshness"] == "fresh"
    assert feed["articles"]
    assert feed["articles"][0]["source_flag"] == "official"
    assert feed["pulse"]["article_count"] == 4
    assert any(cluster["article_count"] >= 2 for cluster in feed["clusters"])


def test_news_intelligence_feed_supports_region_and_source_group_filters():
    reset_app_state_tables()
    service = NewsIntelligenceService(producer=FakeProducer())

    vn_feed = service.get_feed(force=True, region="VN")
    crypto_feed = service.get_feed(source_group="crypto")

    assert [article["region"] for article in vn_feed["articles"]] == ["VN"]
    assert [article["source_group"] for article in crypto_feed["articles"]] == ["crypto"]
    assert vn_feed["selected_filters"]["region"] == "VN"


def test_news_intelligence_public_feed_endpoint(monkeypatch):
    reset_app_state_tables()
    monkeypatch.setattr(
        "risk_dashboard.modules.news_intelligence.application.services.NewsRssProducer.fetch",
        lambda self: FakeProducer().fetch(),
    )
    client = TestClient(app)

    response = client.get("/api/v1/public/news/feed?limit=2&force=true")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["articles"]) == 2
    assert payload["confidence_label"] in {"moderate", "limited"}


def test_news_analyst_chat_uses_news_context(monkeypatch):
    reset_app_state_tables()
    monkeypatch.setenv("NEWS_ANALYST_AGENT_ENABLED", "0")
    monkeypatch.setenv("NEWS_ANALYST_TAVILY_ENABLED", "0")
    monkeypatch.setattr(
        "risk_dashboard.modules.news_intelligence.application.services.NewsRssProducer.fetch",
        lambda self: FakeProducer().fetch(),
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/public/news/chat",
        json={
            "message": "Fed giảm 2% lãi suất thì tác động tới hàng hóa thế nào?",
            "time_range_hours": 168,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["role"] == "news_analyst"
    assert "search_news_articles" in payload["tools_used"]
    assert payload["key_points"]
    assert payload["confidence_label"] in {"moderate", "limited"}
