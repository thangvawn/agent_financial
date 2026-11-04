from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from risk_dashboard.app.bootstrap.app_factory import create_app
from risk_dashboard.modules.data_hub.application.global_market_feed import GlobalMarketFeedProducer
from risk_dashboard.modules.data_hub.application.vn_market_feed import VnMarketFeedProducer
from risk_dashboard.modules.market_portfolio.application import (
    derivatives_feed,
    pricing,
    watchlist_quotes,
)

BASE = "/api/v1/market-portfolio"


@pytest.fixture
def setup(tmp_path, monkeypatch):
    now = datetime.now(timezone.utc).isoformat()
    vn_dir = tmp_path / "vn"
    vn = VnMarketFeedProducer(cache_dir=vn_dir)
    vn.snapshot_path.write_text(
        json.dumps(
            {
                "as_of": now,
                "source": "ssi",
                "items": [
                    {
                        "symbol": "FPT",
                        "name": "FPT Corporation",
                        "price": 96000,
                        "change": 1000,
                        "change_pct": 1.05,
                    },
                    {"symbol": "D2D", "name": "D2D", "price": 22000, "change": 0, "change_pct": 0},
                ],
            }
        )
    )
    vn.universe_path.write_text(json.dumps({"tickers": [{"symbol": "VCB", "name": "Vietcombank"}]}))
    global_dir = tmp_path / "global"
    global_dir.mkdir()
    rows = [
        ("BTC", "crypto", 98000.25, 120.5, 0.12),
        ("SHIB", "crypto", 0.00001234, -0.00000015, -1.2),
        ("EURUSD", "fx", 1.08234, -0.00123, -0.11),
        ("XAU", "commodities", 2345.6, -12.3, -0.52),
        ("SPX", "indices", 5800.1, 20.25, 0.35),
    ]
    global_path = global_dir / "global_market_snapshot.json"
    global_path.write_text(
        json.dumps(
            {
                "as_of": now,
                "items": [
                    {
                        "symbol": symbol,
                        "group": group,
                        "price": price,
                        "change": change,
                        "change_pct": pct,
                        "updated_at": now,
                    }
                    for symbol, group, price, change, pct in rows
                ],
            }
        )
    )
    derivative_path = tmp_path / "derivatives.json"
    derivative_path.write_text(
        json.dumps(
            {
                "as_of": now,
                "items": [
                    {"symbol": "VN30F1M", "price": 1809.3, "change": -48.7, "change_pct": -2.62}
                ],
            }
        )
    )
    monkeypatch.setattr(watchlist_quotes, "_vn", vn)
    monkeypatch.setattr(watchlist_quotes, "_global", GlobalMarketFeedProducer(cache_dir=global_dir))
    monkeypatch.setattr(derivatives_feed, "_CACHE_PATH", derivative_path)
    monkeypatch.setattr(pricing, "_vn", vn)

    def no_network(*args, **kwargs):
        raise AssertionError("Watchlist must read maintained snapshots without a provider request")

    monkeypatch.setattr(vn, "refresh_in_background", no_network)
    monkeypatch.setattr(vn, "_fetch_snapshot_live", no_network)
    monkeypatch.setattr(GlobalMarketFeedProducer, "_fetch_yahoo_snapshot", no_network)
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/public/auth/register",
        json={
            "name": "Watchlist QA",
            "email": f"{uuid4().hex}@qa.test",
            "password": "Test-Only-QA-2026",
        },
    )
    assert response.status_code == 200
    headers = {"Authorization": f"Bearer {response.json()['session_id']}"}
    return client, headers, global_path, vn


@pytest.mark.parametrize(
    "symbol,canonical,price,asset,unit",
    [
        ("FPT", "FPT", 96000, "vn_stocks", "VND"),
        ("BTC-USD", "BTC", 98000.25, "crypto", "USD"),
        ("SHIB", "SHIB", 0.00001234, "crypto", "USD"),
        ("EUR/USD", "EURUSD", 1.08234, "fx", "USD / EUR"),
        ("XAU", "XAU", 2345.6, "commodities", "USD/oz"),
        ("^GSPC", "SPX", 5800.1, "indices", "điểm"),
        ("VN30F1M", "VN30F1M", 1809.3, "derivatives", "điểm"),
    ],
)
def test_add_reload_and_remove_every_asset(setup, symbol, canonical, price, asset, unit):
    client, headers, *_ = setup
    added = client.post(f"{BASE}/watchlist/items", headers=headers, json={"symbol": symbol})
    assert added.status_code == 200
    assert added.json()["symbol"] == canonical
    rows = client.get(f"{BASE}/watchlist", headers=headers).json()["items"]
    assert len(rows) == 1
    assert (rows[0]["price"], rows[0]["asset_class"], rows[0]["unit"]) == (price, asset, unit)
    assert rows[0]["quote_status"] == "available"
    client.post(f"{BASE}/watchlist/items", headers=headers, json={"symbol": canonical.lower()})
    assert len(client.get(f"{BASE}/watchlist", headers=headers).json()["items"]) == 1
    assert client.delete(f"{BASE}/watchlist/items/{canonical}", headers=headers).json()["removed"]
    assert client.get(f"{BASE}/watchlist", headers=headers).json()["items"] == []


def test_catalog_and_missing_quotes_never_drop_saved_items(setup):
    client, headers, _, vn = setup
    catalog = {
        item["symbol"]: item
        for item in client.get(f"{BASE}/watchlist/instruments", headers=headers).json()["items"]
    }
    assert {"BTC", "EURUSD", "XAU", "SPX", "VN30F1M", "FPT", "D2D", "VCB"} <= catalog.keys()
    for symbol in ["ETH", "VCB", "UNKNOWN"]:
        assert (
            client.post(
                f"{BASE}/watchlist/items", headers=headers, json={"symbol": symbol}
            ).status_code
            == 200
        )
    vn.snapshot_path.write_text("{}")
    items = client.get(f"{BASE}/watchlist", headers=headers).json()["items"]
    assert len(items) == 3
    assert all(item["price"] is None and item["quote_status"] == "unavailable" for item in items)


def test_one_broken_feed_does_not_hide_other_assets(setup):
    client, headers, path, _ = setup
    for symbol in ["BTC", "FPT"]:
        client.post(f"{BASE}/watchlist/items", headers=headers, json={"symbol": symbol})
    path.write_text("broken cache")
    items = {
        i["symbol"]: i for i in client.get(f"{BASE}/watchlist", headers=headers).json()["items"]
    }
    assert items["BTC"]["price"] is None
    assert items["FPT"]["price"] == 96000


def test_quote_time_takes_precedence_over_recent_snapshot(setup):
    client, headers, path, _ = setup
    payload = json.loads(path.read_text())
    old = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    payload["items"][0]["updated_at"] = old
    path.write_text(json.dumps(payload))
    item = client.post(f"{BASE}/watchlist/items", headers=headers, json={"symbol": "BTC"}).json()
    assert item["quote_status"] == "stale"
    assert item["updated_at"] == old
    assert item["price"] == 98000.25


def test_account_isolation_and_paper_trading_stays_vnd_only(setup):
    client, headers, *_ = setup
    client.post(f"{BASE}/watchlist/items", headers=headers, json={"symbol": "BTC"})
    other = client.post(
        "/api/v1/public/auth/register",
        json={"name": "Other", "email": f"{uuid4().hex}@qa.test", "password": "Test-Only-QA-2026"},
    ).json()
    other_headers = {"Authorization": f"Bearer {other['session_id']}"}
    assert client.get(f"{BASE}/watchlist", headers=other_headers).json()["items"] == []
    assert not client.delete(f"{BASE}/watchlist/items/BTC", headers=other_headers).json()["removed"]
    assert len(client.get(f"{BASE}/watchlist", headers=headers).json()["items"]) == 1
    order = client.post(
        f"{BASE}/orders",
        headers=headers,
        json={"symbol": "BTC", "side": "BUY", "order_type": "MP", "quantity": 1},
    )
    assert order.status_code == 400
    assert client.get(f"{BASE}/watchlist/instruments").status_code == 401


def test_legacy_slash_alias_can_be_read_deduplicated_and_removed(setup):
    client, headers, *_ = setup
    profile = client.get("/api/v1/public/auth/me", headers=headers).json()["profile"]
    from risk_dashboard.modules.market_portfolio.infrastructure.repository import (
        MarketPortfolioRepository,
    )

    MarketPortfolioRepository().add_watchlist(profile["account_id"], "EUR/USD")
    items = client.get(f"{BASE}/watchlist", headers=headers).json()["items"]
    assert items[0]["price"] == 1.08234
    assert items[0]["symbol"] == "EUR/USD"
    client.post(f"{BASE}/watchlist/items", headers=headers, json={"symbol": "EURUSD"})
    assert len(client.get(f"{BASE}/watchlist", headers=headers).json()["items"]) == 1
    removed = client.delete(f"{BASE}/watchlist/items/EUR%2FUSD", headers=headers)
    assert removed.status_code == 200
    assert removed.json()["removed"]
