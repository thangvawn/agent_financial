from __future__ import annotations

from fastapi.testclient import TestClient

from risk_dashboard.app.bootstrap.app_factory import create_app
from risk_dashboard.modules.market_portfolio.application.fills import resolve_fill_price
from risk_dashboard.modules.market_portfolio.domain.entities import PaperOrder
from risk_dashboard.platform.database import open_app_state_db, reset_app_state_tables


def _client() -> TestClient:
    return TestClient(create_app())


def test_resolve_fill_price_mp_and_lo():
    order = PaperOrder(
        order_id="1",
        user_id="u",
        symbol="FPT",
        side="BUY",
        order_type="MP",
        quantity=10,
        limit_price=None,
        status="OPEN",
        filled_qty=0,
        filled_price=None,
        created_at="t",
        updated_at="t",
        filled_at=None,
    )
    assert resolve_fill_price(order, 100.0) == 100.0
    order.order_type = "LO"
    order.limit_price = 95.0
    assert resolve_fill_price(order, 100.0) is None
    assert resolve_fill_price(order, 90.0) == 90.0


def test_market_portfolio_watchlist_and_portfolio_flow(monkeypatch):
    reset_app_state_tables()
    # Ensure schema has mp_* tables
    with open_app_state_db() as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert "mp_watchlist_items" in tables
    assert "mp_orders" in tables

    from risk_dashboard.modules.market_portfolio.application import services as svc_mod

    monkeypatch.setattr(svc_mod, "quote_last_price", lambda symbol: 100_000.0 if symbol == "FPT" else None)
    monkeypatch.setattr(svc_mod, "quote_map", lambda symbols: {s: 100_000.0 for s in symbols if s == "FPT"})

    client = _client()
    session = "test-session-market-portfolio-001"

    added = client.post(
        "/api/v1/market-portfolio/watchlist/items",
        json={"session_id": session, "symbol": "FPT"},
    )
    assert added.status_code == 200
    assert added.json()["symbol"] == "FPT"

    watchlist = client.get(f"/api/v1/market-portfolio/watchlist?session_id={session}")
    assert watchlist.status_code == 200
    assert any(i["symbol"] == "FPT" for i in watchlist.json()["items"])

    order = client.post(
        "/api/v1/market-portfolio/orders",
        json={
            "session_id": session,
            "symbol": "FPT",
            "side": "BUY",
            "order_type": "MP",
            "quantity": 10,
        },
    )
    assert order.status_code == 200
    body = order.json()
    assert body["status"] == "FILLED"
    assert body["filled_price"] == 100_000.0

    portfolio = client.get(f"/api/v1/market-portfolio/portfolio?session_id={session}")
    assert portfolio.status_code == 200
    summary = portfolio.json()
    assert summary["cash_balance"] == 100_000_000.0 - 1_000_000.0
    assert any(p["symbol"] == "FPT" and p["quantity"] == 10 for p in summary["positions"])

    terminal = client.get("/api/v1/market-portfolio/market-data/terminal?view=dashboard")
    assert terminal.status_code == 200
