"""Partial-provider regressions use only mocks and per-test cache directories."""

import json
from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from risk_dashboard.modules.data_hub.application import global_market_feed
from risk_dashboard.modules.data_hub.application import vn_market_feed as feed


@pytest.fixture
def environment(tmp_path, monkeypatch):
    producer = feed.VnMarketFeedProducer(cache_dir=tmp_path)
    rows = [
        {"symbol": s, "name": s, "exchange": ex, "price": 10000, "change_pct": 0, "volume": 100}
        for s, ex in [("AAA", "HOSE"), ("BBB", "HNX"), ("CCC", "UPCOM")]
    ]
    monkeypatch.setattr(producer, "universe", lambda: {"tickers": rows})
    monkeypatch.setattr(feed, "_cached_profile_shares", lambda _: {})
    monkeypatch.setenv("VN_MARKET_PROVIDER", "ssi")
    monkeypatch.setattr(
        global_market_feed, "_VNSTOCK_RATE_LIMITER", SimpleNamespace(acquire=lambda: None)
    )
    monkeypatch.setattr(global_market_feed, "_vnstock_safe", nullcontext)
    import sys

    monkeypatch.setitem(
        sys.modules,
        "vnstock",
        SimpleNamespace(Trading=lambda **_: SimpleNamespace(price_board=lambda _: None)),
    )
    monkeypatch.setattr(feed, "_fetch_vci_price_board", lambda _: [])
    return producer, rows


@pytest.mark.parametrize("failure", ["timeout", "empty", "malformed"])
def test_ssi_rejects_a_missing_exchange_and_preserves_complete_cache(
    environment, monkeypatch, failure
):
    producer, rows = environment
    cached = {
        "as_of": "2026-11-02T00:00:00+00:00",
        "source": "ssi",
        "freshness": "fresh",
        "items": rows,
    }
    producer.snapshot_path.write_text(json.dumps(cached))
    previous = producer.snapshot_path.read_bytes()

    def get(url, **_):
        ex = url.rsplit("/", 1)[1]
        if ex == "hnx":
            if failure == "timeout":
                raise feed.requests.Timeout("test HNX timeout")
            payload = {"data": []} if failure == "empty" else {"data": "invalid"}
        else:
            payload = {
                "data": [
                    {
                        "stockSymbol": {"hose": "AAA", "upcom": "CCC"}[ex],
                        "exchange": ex,
                        "matchedPrice": 10000,
                        "refPrice": 10000,
                        "nmTotalTradedQty": 100,
                    }
                ]
            }
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: payload)

    monkeypatch.setattr(feed.requests, "get", get)
    result = producer.snapshot(force_refresh=True)
    assert result["freshness"] == "stale"
    assert [r["symbol"] for r in result["items"]] == ["AAA", "BBB", "CCC"]
    assert result["last_success_at"] == cached["as_of"]
    assert producer.snapshot_path.read_bytes() == previous


def test_fallback_must_cover_all_exchanges_before_replacing_cache(environment, monkeypatch):
    producer, rows = environment
    monkeypatch.setattr(feed, "_fetch_ssi_price_board", lambda: rows[:1])
    monkeypatch.setattr(
        feed, "_fetch_vci_price_board", lambda _: [{**r, "source": "vci_http"} for r in rows]
    )
    result = producer.snapshot(force_refresh=True)
    assert result["source"] == "vci_http"
    assert result["freshness"] == "fresh"
    assert len(json.loads(producer.snapshot_path.read_text())["items"]) == 3


def test_cold_start_never_claims_a_partial_market_is_fresh(environment, monkeypatch):
    producer, rows = environment
    monkeypatch.setattr(feed, "_fetch_ssi_price_board", lambda: rows[:1])
    monkeypatch.setattr(feed, "_fetch_vci_price_board", lambda _: rows[1:])
    result = producer.snapshot(force_refresh=True)
    assert result["freshness"] == "degraded"
    assert result["items"] == []
    assert not producer.snapshot_path.exists()


def test_snapshot_commit_checks_coverage_even_if_a_provider_reports_fresh(environment, monkeypatch):
    producer, rows = environment
    cached = {"as_of": "2026-11-02T00:00:00+00:00", "freshness": "fresh", "items": rows}
    producer.snapshot_path.write_text(json.dumps(cached))
    previous = producer.snapshot_path.read_bytes()
    monkeypatch.setattr(
        producer,
        "_fetch_snapshot_live",
        lambda: {"as_of": "2026-11-02T01:00:00+00:00", "freshness": "fresh", "items": rows[:1]},
    )
    result = producer.snapshot(force_refresh=True)
    assert result["freshness"] == "stale"
    assert len(result["items"]) == 3
    assert producer.snapshot_path.read_bytes() == previous
