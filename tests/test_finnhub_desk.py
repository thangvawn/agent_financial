from __future__ import annotations

from risk_dashboard.modules.news_intelligence.application.finnhub_desk import get_finnhub_desk_snapshot


def test_finnhub_desk_disabled_without_api_key(monkeypatch):
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    out = get_finnhub_desk_snapshot(force=False)
    assert out["enabled"] is False
    assert out["reason"] == "missing_api_key"
    assert out["calendar"] is None
    assert out["quotes"] is None
