from fastapi.testclient import TestClient

from risk_dashboard.api.main import app


def test_simulation_lab_studio_bootstrap_and_run(monkeypatch, tmp_path):
    monkeypatch.setenv("MODE", "test")
    monkeypatch.setenv("PRO_LAB_LOCAL_TEST_OPEN", "1")
    monkeypatch.setenv("RISK_DASHBOARD_DB_PATH", str(tmp_path / "studio.sqlite3"))

    def fake_backtest(tickers, start, end, initial_capital, **kwargs):
        return {
            "tickers": tickers,
            "interval": kwargs["interval"],
            "weights": {ticker: 1 / len(tickers) for ticker in tickers},
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "initial_capital": initial_capital,
            "metrics": {"total_return_pct": 10.0, "max_drawdown_pct": -5.0, "sharpe": 1.1},
            "series": {
                "portfolio": [
                    {"time": 1672531200, "value": initial_capital},
                    {"time": 1704067200, "value": initial_capital * 1.1},
                ]
            },
            "monthly_returns": [],
            "ath_segments": [],
            "benchmark_label": "VN-Index",
            "warnings": [],
            "source": "test_historical_feed",
        }

    monkeypatch.setattr(
        "risk_dashboard.modules.pro_lab.application.services.run_vn_portfolio_backtest",
        fake_backtest,
    )
    client = TestClient(app)

    bootstrap = client.get("/api/v1/pro/pro-lab/studio/bootstrap?user_id=studio-tester")
    assert bootstrap.status_code == 200
    assert bootstrap.json()["execution_profile"]["defaults"]["lot_size"] == 100
    assert len(bootstrap.json()["templates"]) >= 2

    run = client.post(
        "/api/v1/pro/pro-lab/studio/runs",
        json={
            "user_id": "studio-tester",
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
            "strategy": {
                "name": "VN Trend Test",
                "hypothesis": "Kiểm thử xu hướng trên dữ liệu lịch sử Việt Nam.",
                "universe": ["FPT", "VCB"],
                "benchmark": "VNINDEX",
                "entry_rules": [{"field": "close", "operator": "above", "value": "sma_20"}],
                "exit_rules": [{"field": "close", "operator": "below", "value": "sma_20"}],
            },
            "execution": {"initial_capital": 100_000_000, "timeframe": "1d"},
        },
    )
    assert run.status_code == 200
    payload = run.json()
    assert payload["experiment"]["engine_result"]["metrics"]["total_return_pct"] == 10.0
    assert payload["fidelity"]["costs_applied"] is False

    refreshed = client.get("/api/v1/pro/pro-lab/studio/bootstrap?user_id=studio-tester")
    assert len(refreshed.json()["workspace"]["experiments"]) == 1
