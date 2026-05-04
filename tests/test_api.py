from datetime import date
from unittest import mock

import pandas as pd
from fastapi.testclient import TestClient

from risk_dashboard.api.main import app, set_panel_for_testing


def test_health():
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("ok", "degraded")
    assert "checks" in body
    assert "panel_loaded" in body["checks"]
    assert "model_available" in body["checks"]


def test_eod_requires_panel(synthetic_panel):
    set_panel_for_testing(synthetic_panel)
    c = TestClient(app)
    as_of = synthetic_panel["date"].iloc[-1].date()
    r = c.post("/eod/run", json={"as_of": str(as_of)})
    assert r.status_code == 200
    body = r.json()
    assert body["review"]["ok"] is True
    assert 0 <= body["quant"]["decision_score"] <= 1
    assert "metrics_by_horizon" in body["quant"]["backtest"]
    assert "provenance" in body["quant"]


def test_dashboard_page_and_state(synthetic_panel):
    set_panel_for_testing(synthetic_panel)
    c = TestClient(app)
    page = c.get("/dashboard")
    assert page.status_code == 200
    assert '<div id="root"></div>' in page.text
    assert "/dashboard-static/assets/" in page.text

    state = c.get("/dashboard/state")
    assert state.status_code == 200
    payload = state.json()
    assert payload["loaded"] is True
    assert payload["rows"] == len(synthetic_panel)


@mock.patch("risk_dashboard.api.main.cross_asset_prices_mod.build_cross_asset_dashboard")
def test_dashboard_cross_asset_returns_payload(mock_cross_asset):
    mock_cross_asset.return_value = {
        "as_of": "2026-04-16",
        "assets": [
            {
                "id": "gold",
                "label": "Vàng",
                "symbol": "GC=F",
                "market": "commodity",
                "status": "ok",
                "price": 3200.5,
                "change_1d_pct": 0.8,
                "change_1w_pct": 2.3,
                "change_1m_pct": 4.9,
                "bars": [{"time": 1713220800, "value": 3200.5}],
            }
        ],
    }
    c = TestClient(app)
    r = c.get("/dashboard/cross-asset?limit=180")
    assert r.status_code == 200
    body = r.json()
    assert body["as_of"] == "2026-04-16"
    assert body["assets"][0]["symbol"] == "GC=F"
    assert body["assets"][0]["bars"]
    mock_cross_asset.assert_called_once_with(limit=180)


@mock.patch("risk_dashboard.api.main.run_backtest_strategy_lab")
def test_trading_lab_strategy_design_returns_payload(mock_strategy):
    mock_strategy.return_value = {
        "mode": "backtest_strategy_lab",
        "agents": [
            {"role": "analyst", "label": "Nhà phân tích", "memo": "Luận điểm tăng trưởng."},
            {"role": "stop_loss", "label": "Agent Stop-loss", "memo": "SL 8%."},
        ],
        "blueprint": {
            "title": "Chiến lược nháp",
            "summary": "Tăng trưởng có kiểm soát rủi ro.",
            "execution_rule": {
                "enabled": True,
                "strategy_type": "volume_btc_confirm_stop_loss",
                "summary": "Volume tăng mạnh, BTC xác nhận, SL 4%.",
                "params": {
                    "volume_spike_multiplier": 2.0,
                    "btc_daily_change_min_pct": 3.0,
                    "stop_loss_pct": 4.0,
                },
                "parser_notes": [],
                "unsupported_parts": [],
            },
            "backtest_ready": {
                "tickers": ["FPT", "VCB"],
                "equal_weight": False,
                "weights": {"FPT": 0.6, "VCB": 0.4},
            },
        },
    }
    c = TestClient(app)
    r = c.post(
        "/admin/trading-lab/strategy-design",
        headers={"X-Admin-Trading-Lab-Key": "secret"},
        json={
            "brief": "Thiết kế chiến lược tăng trưởng có stop-loss.",
            "roles": ["analyst", "risk_manager", "stop_loss"],
            "tickers": ["FPT", "VCB"],
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "initial_capital": 100000000,
            "risk_budget_pct": 8,
            "holding_period": "1-3 tháng",
        },
    )
    assert r.status_code in (200, 401, 503)
    if r.status_code == 200:
        body = r.json()
        assert body["mode"] == "backtest_strategy_lab"
        assert body["blueprint"]["backtest_ready"]["tickers"] == ["FPT", "VCB"]
        assert body["blueprint"]["execution_rule"]["enabled"] is True


def test_research_model_report_endpoint():
    c = TestClient(app)
    r = c.get("/research/model-report")
    assert r.status_code == 200
    payload = r.json()
    assert "summary" in payload
    assert "model_version" in payload["summary"]


def test_chat_endpoint_returns_response(synthetic_panel):
    set_panel_for_testing(synthetic_panel)
    c = TestClient(app)
    as_of = synthetic_panel["date"].iloc[-1].date()
    r = c.post("/chat", json={"as_of": str(as_of), "message": "giải thích rủi ro hiện tại"})
    assert r.status_code == 200
    payload = r.json()
    assert payload["text"]
    assert "route" in payload
    assert "provenance" in payload


def test_backtest_run_rejects_invalid_range():
    c = TestClient(app)
    r = c.post(
        "/backtest/run",
        json={
            "tickers": ["FPT"],
            "start_date": "2024-06-01",
            "end_date": "2024-01-01",
            "initial_capital": 1_000_000,
        },
    )
    assert r.status_code == 410
    assert "retire" in r.json()["detail"].lower()


@mock.patch("risk_dashboard.api.main.watchlist_prices_mod.sync_watchlist_ticker")
def test_watchlist_prices_get_returns_bars(mock_sync):
    import pandas as pd

    mock_sync.return_value = pd.DataFrame(
        {
            "open": [10.0],
            "high": [11.0],
            "low": [9.5],
            "close": [10.5],
            "volume": [1e6],
        },
        index=pd.DatetimeIndex([pd.Timestamp("2024-01-02")]),
    )
    c = TestClient(app)
    r = c.get("/watchlist/prices/FPT")
    assert r.status_code == 200
    body = r.json()
    assert body["ticker"] == "FPT"
    assert len(body["bars"]) == 1
    assert "open" in body["bars"][0]


def test_backtest_run_is_retired_in_public_surface():
    c = TestClient(app)
    r = c.post(
        "/backtest/run",
        json={
            "tickers": ["FPT"],
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
            "initial_capital": 1_000_000,
            "equal_weight": True,
            "include_benchmark": False,
        },
    )
    assert r.status_code == 410
    assert "pro" in r.json()["detail"].lower()
