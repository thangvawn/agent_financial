from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from risk_dashboard.modules.data_hub.application import vn_market_feed
from risk_dashboard.modules.data_hub.application.vn_market_feed import (
    VnMarketFeedProducer,
    _fetch_vci_price_board,
)


def _timestamp(delta_seconds: int = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(seconds=delta_seconds)).isoformat()


def test_feed_uses_instance_cache_dir_and_atomic_refresh(tmp_path: Path, monkeypatch) -> None:
    producer = VnMarketFeedProducer(cache_dir=tmp_path, snapshot_ttl_seconds=60)
    live = {
        "as_of": _timestamp(),
        "source": "test",
        "freshness": "fresh",
        "items": [{"symbol": "FPT", "price": 100000}],
    }
    monkeypatch.setattr(producer, "_fetch_snapshot_live", lambda: live)

    result = producer.snapshot(force_refresh=True)

    assert result == live
    assert producer.snapshot_path == tmp_path / "snapshot.json"
    assert producer.snapshot_path.exists()
    assert producer.snapshot_path.read_text(encoding="utf-8").startswith("{")


def test_stale_snapshot_is_served_while_refresh_runs_in_background(tmp_path: Path, monkeypatch) -> None:
    producer = VnMarketFeedProducer(cache_dir=tmp_path, snapshot_ttl_seconds=1)
    producer._write_json(
        producer.snapshot_path,
        {
            "as_of": _timestamp(120),
            "source": "test",
            "items": [{"symbol": "FPT", "price": 99000}],
        },
    )
    refresh_called = False

    def _refresh():
        nonlocal refresh_called
        refresh_called = True
        return None

    monkeypatch.setattr(producer, "refresh_in_background", _refresh)
    result = producer.snapshot()

    assert refresh_called is True
    assert result["freshness"] == "stale"
    assert result["stale_reason"] == "live_feed_unavailable_using_cache"
    assert result["items"][0]["symbol"] == "FPT"


def test_universe_refresh_uses_custom_cache_dir(tmp_path: Path, monkeypatch) -> None:
    producer = VnMarketFeedProducer(cache_dir=tmp_path, universe_ttl_seconds=1)
    live = {
        "as_of": _timestamp(),
        "source": "test",
        "tickers": [{"symbol": "FPT", "name": "FPT", "exchange": "HOSE"}],
    }
    monkeypatch.setattr(producer, "_fetch_universe_live", lambda: live)

    result = producer.universe(force_refresh=True)

    assert result["freshness"] == "fresh"
    assert result["tickers"][0]["symbol"] == "FPT"
    assert producer.universe_path.exists()


def test_off_hours_uses_slow_ttl_without_provider_stampede(tmp_path: Path, monkeypatch) -> None:
    producer = VnMarketFeedProducer(cache_dir=tmp_path, snapshot_ttl_seconds=15)
    producer._write_json(
        producer.snapshot_path,
        {
            "as_of": _timestamp(30),
            "source": "vci_http",
            "freshness": "fresh",
            "items": [{"symbol": "FPT", "price": 100000}],
        },
    )
    monkeypatch.setattr(vn_market_feed, "_is_vn_market_hours", lambda: False)
    monkeypatch.setenv("VN_MARKET_INTERVAL_SLOW_SEC", "300")
    monkeypatch.setattr(producer, "refresh_in_background", lambda: (_ for _ in ()).throw(AssertionError("unexpected refresh")))

    result = producer.snapshot()

    assert result["freshness"] == "fresh"
    assert result["items"][0]["symbol"] == "FPT"


def test_vci_http_price_board_fallback_normalizes_quote(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return [
                {
                    "listingInfo": {
                        "symbol": "FPT",
                        "organName": "FPT Corporation",
                        "board": "HSX",
                        "refPrice": 65000,
                        "ceiling": 70000,
                        "floor": 60000,
                        "listedShare": 1000000,
                    },
                    "matchPrice": {
                        "matchPrice": 66000,
                        "matchVol": 1200,
                        "accumulatedVolume": 9000,
                        "accumulatedValue": 594000,
                        "foreignBuyVolume": 100,
                        "foreignSellVolume": 50,
                    },
                    "bidAsk": {
                        "bidPrices": [{"price": 65900, "volume": 10}],
                        "askPrices": [{"price": 66100, "volume": 20}],
                    },
                }
            ]

    monkeypatch.setattr(vn_market_feed.requests, "post", lambda *args, **kwargs: FakeResponse())

    result = _fetch_vci_price_board(["FPT"])

    assert result[0]["symbol"] == "FPT"
    assert result[0]["change"] == 1000
    assert result[0]["change_pct"] == 1.538
    assert result[0]["bid_1_price"] == 65900
    assert result[0]["ask_1_volume"] == 20
    assert result[0]["market_cap"] == 66.0


def test_ssi_price_board_normalizes_quote(monkeypatch) -> None:
    class FakeSsiResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "code": "SUCCESS",
                "data": [
                    {
                        "stockSymbol": "SSI",
                        "companyNameVi": "Công ty Cổ phần Chứng khoán SSI",
                        "exchange": "hose",
                        "refPrice": 30000,
                        "matchedPrice": 31500,
                        "ceiling": 32100,
                        "floor": 27900,
                        "priceChange": 1500,
                        "priceChangePercent": 5.0,
                        "openPrice": 30500,
                        "highest": 31800,
                        "lowest": 30200,
                        "matchedVolume": 50000,
                        "nmTotalTradedQty": 12000000,
                        "nmTotalTradedValue": 375000000000,
                        "buyForeignQtty": 500000,
                        "sellForeignQtty": 200000,
                        "best1Bid": 31450,
                        "best1BidVol": 150000,
                        "best1Offer": 31500,
                        "best1OfferVol": 80000,
                    }
                ],
            }

    monkeypatch.setattr(vn_market_feed.requests, "get", lambda *args, **kwargs: FakeSsiResponse())

    from risk_dashboard.modules.data_hub.application.vn_market_feed import _fetch_ssi_price_board

    result = _fetch_ssi_price_board(exchanges=("hose",))

    assert len(result) == 1
    assert result[0]["symbol"] == "SSI"
    assert result[0]["name"] == "Công ty Cổ phần Chứng khoán SSI"
    assert result[0]["exchange"] == "HOSE"
    assert result[0]["price"] == 31500
    assert result[0]["change"] == 1500
    assert result[0]["change_pct"] == 5.0
    assert result[0]["bid_1_price"] == 31450
    assert result[0]["bid_1_volume"] == 150000
    assert result[0]["ask_1_price"] == 31500
    assert result[0]["ask_1_volume"] == 80000
    assert result[0]["source"] == "ssi"
