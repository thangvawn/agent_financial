"""Integration tests — full EOD pipeline through API."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def loaded_client(synthetic_panel):
    from risk_dashboard.api.main import app, set_panel_for_testing
    set_panel_for_testing(synthetic_panel)
    return TestClient(app)


def test_full_eod_via_api(loaded_client, as_of_date):
    resp = loaded_client.post(
        "/eod/run",
        json={"as_of": as_of_date.isoformat()},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "quant" in body or "decision_score" in body
    quant = body.get("quant", body)
    assert 0 <= quant["decision_score"] <= 1
    assert quant["horizons"]["p_decline_1w"] >= 0
    assert quant["horizons"]["p_decline_2w"] >= 0
    assert quant["horizons"]["p_decline_1m"] >= 0


def test_dashboard_state_when_loaded(loaded_client):
    resp = loaded_client.get("/dashboard/state")
    assert resp.status_code == 200
    body = resp.json()
    assert body["loaded"] is True
    assert body["rows"] > 0
    assert body["start_date"] is not None


def test_scenario_rerun_via_api(loaded_client, as_of_date):
    resp = loaded_client.post(
        "/scenario/rerun",
        json={
            "as_of": as_of_date.isoformat(),
            "usd_vnd_rate": 25500.0,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    quant = body.get("quant", body)
    assert "decision_score" in quant


def test_history_returns_data(loaded_client):
    resp = loaded_client.get("/dashboard/history?limit=10")
    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
