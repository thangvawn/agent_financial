from datetime import date

import pandas as pd
from fastapi.testclient import TestClient

from risk_dashboard.api.main import app, set_panel_for_testing


def test_health():
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


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
