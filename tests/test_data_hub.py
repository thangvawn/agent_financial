from fastapi.testclient import TestClient

from risk_dashboard.api.main import app


def fake_feed_snapshot(self):
    items = [
        {"symbol": "SPX", "name": "S&P 500", "group": "indices", "price": 5000, "change": 10, "change_pct": 0.2, "focus": "US breadth", "source": "test", "updated_at": "2026-04-20T00:00:00+00:00"},
        {"symbol": "DXY", "name": "Dollar Index", "group": "fx", "price": 100, "change": -0.1, "change_pct": -0.1, "focus": "USD", "source": "test", "updated_at": "2026-04-20T00:00:00+00:00"},
        {"symbol": "XAU", "name": "Gold", "group": "commodities", "price": 2400, "change": 12, "change_pct": 0.5, "focus": "Safe haven", "source": "test", "updated_at": "2026-04-20T00:00:00+00:00"},
        {"symbol": "BTC", "name": "Bitcoin", "group": "crypto", "price": 70000, "change": 700, "change_pct": 1.0, "focus": "Risk appetite", "source": "test", "updated_at": "2026-04-20T00:00:00+00:00"},
    ]
    return {
        "as_of": "2026-04-20T00:00:00+00:00",
        "source": "test_feed",
        "freshness": "fresh",
        "stale_reason": None,
        "groups": {
            "indices": [item for item in items if item["group"] == "indices"],
            "fx": [item for item in items if item["group"] == "fx"],
            "commodities": [item for item in items if item["group"] == "commodities"],
            "crypto": [item for item in items if item["group"] == "crypto"],
        },
    }


def fake_news_feed(self, **kwargs):
    return {
        "as_of": "2026-04-20T00:00:00+00:00",
        "freshness": "fresh",
        "confidence_label": "moderate",
        "stale_reason": None,
        "source_count": 2,
        "successful_source_count": 2,
        "articles": [
            {
                "id": "news_1",
                "article_id": "news_1",
                "time": "09:30",
                "headline": "Fed signals rate patience as markets digest inflation risk",
                "summary": "Policy makers remain cautious.",
                "source": "Federal Reserve",
                "source_id": "fed_press",
                "source_tier": 1,
                "source_flag": "official",
                "region": "US",
                "category": "macro",
                "url": "https://example.com/fed",
                "published_at": "2026-04-20T09:30:00+00:00",
                "fetched_at": "2026-04-20T09:31:00+00:00",
                "sort_ts": 1776677400,
                "priority": 4,
                "sentiment": "neutral",
                "impact": "high",
                "tickers": [],
                "language": "en",
                "threat_level": "normal",
                "threat_category": None,
                "threat_confidence": 0,
            }
        ],
        "clusters": [],
        "pulse": {"article_count": 1, "high_impact_count": 1},
    }


def test_data_hub_global_terminal_contract(monkeypatch):
    monkeypatch.setattr(
        "risk_dashboard.modules.data_hub.application.services.GlobalMarketFeedProducer.snapshot",
        fake_feed_snapshot,
    )
    monkeypatch.setattr(
        "risk_dashboard.modules.data_hub.application.services.NewsIntelligenceService.get_feed",
        fake_news_feed,
    )
    client = TestClient(app)
    response = client.get("/api/v1/public/data-hub/global-terminal")

    assert response.status_code == 200
    payload = response.json()
    assert payload["terminal"]["status"] == "ready"
    assert payload["trust"]["what_this_is"]
    assert payload["trust"]["what_this_is_not"]
    assert payload["widgets"]["global_indices"]
    assert payload["widgets"]["fx_majors"]
    assert payload["widgets"]["market_pulse"]["fear_greed"] >= 0
    assert payload["widgets"]["market_news"][0]["source_flag"] == "official"
    assert payload["terminal"]["active_view"] == "dashboard"
    assert any(tab["id"] == "crypto" for tab in payload["navigation"]["tabs"])
    assert payload["topics"]


def test_data_hub_global_terminal_view_metadata(monkeypatch):
    monkeypatch.setattr(
        "risk_dashboard.modules.data_hub.application.services.GlobalMarketFeedProducer.snapshot",
        fake_feed_snapshot,
    )
    monkeypatch.setattr(
        "risk_dashboard.modules.data_hub.application.services.NewsIntelligenceService.get_feed",
        fake_news_feed,
    )
    client = TestClient(app)
    response = client.get("/api/v1/public/data-hub/global-terminal?view=crypto")

    assert response.status_code == 200
    payload = response.json()
    assert payload["terminal"]["active_view"] == "crypto"
    assert payload["terminal"]["default_symbol"] == "BTC"
    assert "crypto" in payload["terminal"]["visible_widget_keys"]
    assert "global_indices" not in payload["terminal"]["visible_widget_keys"]


def test_vn_snapshot_returns_exchange_market_summary(monkeypatch):
    monkeypatch.setattr(
        "risk_dashboard.modules.data_hub.api.public._vn_market.snapshot",
        lambda: {
            "as_of": "2026-07-21T04:00:00+00:00",
            "source": "test",
            "freshness": "fresh",
            "count": 4,
            "items": [
                {"symbol": "AAA", "exchange": "HSX", "change_pct": 1.2, "value": 1200},
                {"symbol": "BBB", "exchange": "HOSE", "change_pct": -0.4, "value": 800},
                {"symbol": "CCC", "exchange": "HNX", "change_pct": 0, "value": 500},
                {"symbol": "DDD", "exchange": "UPCOM", "change_pct": None, "value": 100},
            ],
        },
    )
    client = TestClient(app)
    response = client.get("/api/v1/public/data-hub/vn-market/snapshot?limit=2")

    assert response.status_code == 200
    summary = response.json()["market_summary"]
    assert summary["HSX"] == {
        "exchange": "HSX",
        "advances": 1,
        "unchanged": 0,
        "declines": 1,
        "quoted": 2,
        "turnover_billion": 2.0,
    }
    assert summary["HNX"]["unchanged"] == 1
    assert summary["UPCOM"]["quoted"] == 0


def test_data_hub_topic_status_and_lookup(monkeypatch):
    monkeypatch.setattr(
        "risk_dashboard.modules.data_hub.application.services.GlobalMarketFeedProducer.snapshot",
        fake_feed_snapshot,
    )
    monkeypatch.setattr(
        "risk_dashboard.modules.data_hub.application.services.NewsIntelligenceService.get_feed",
        fake_news_feed,
    )
    client = TestClient(app)
    status = client.get("/api/v1/public/data-hub/topics")

    assert status.status_code == 200
    topics = status.json()["topics"]
    assert any(topic["topic"] == "global:indices" for topic in topics)

    topic = client.get("/api/v1/public/data-hub/topics/global:indices")
    assert topic.status_code == 200
    assert topic.json()["payload"]["items"]


def test_global_terminal_direct_route_serves_spa():
    client = TestClient(app)
    response = client.get("/global-terminal")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "root" in response.text
