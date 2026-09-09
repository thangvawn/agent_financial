from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.pro_lab.api.ai import get_ai_provider
from risk_dashboard.platform.ai_runtime.contracts import ModelError
from risk_dashboard.platform.ai_runtime.testing.fake_provider import FakeProvider
from risk_dashboard.platform.security.access_control import assign_role, issue_token_for_actor


@pytest.fixture(autouse=True)
def _clean_overrides():
    yield
    app.dependency_overrides.clear()


def _valid_token() -> str:
    assign_role(actor_id="stream-test-user", role="pro_lab_user")
    token = issue_token_for_actor(actor_id="stream-test-user", role="pro_lab_user", ttl_hours=1)
    return token.token_id


def test_pro_lab_streaming_endpoint_via_testclient():
    token = _valid_token()
    fake_tokens = [
        "{\"strategy_name\": \"VN Momentum\", ",
        "\"market\": \"Vietnam\", ",
        "\"universe\": [\"VCB\", \"FPT\"]}",
    ]
    fake = FakeProvider(scripted_streams=[fake_tokens])
    app.dependency_overrides[get_ai_provider] = lambda: fake
    client = TestClient(app)

    res = client.post(
        "/api/v1/pro/pro-lab/ai/strategy-copilot/stream",
        headers={"X-Access-Token": token},
        json={
            "idea": "Momentum strategy on VN30",
            "market": "Vietnam equities",
            "horizon": "monthly",
            "risk_budget_pct": 2.0,
        },
    )
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]
    assert res.headers["cache-control"] == "no-cache"
    assert res.headers["x-accel-buffering"] == "no"
    text = res.text
    assert "event: start" in text
    assert "event: token" in text
    assert "event: completed" in text


def test_pro_lab_streaming_endpoint_emits_failure_event():
    token = _valid_token()
    fake = FakeProvider(scripted_streams=[ModelError("provider_unavailable", "Service down")])
    app.dependency_overrides[get_ai_provider] = lambda: fake
    client = TestClient(app)

    res = client.post(
        "/api/v1/pro/pro-lab/ai/strategy-copilot/stream",
        headers={"X-Access-Token": token},
        json={"idea": "Momentum strategy on VN30"},
    )

    assert res.status_code == 200
    assert "event: failed" in res.text
    assert '"error_code":"provider_unavailable"' in res.text
