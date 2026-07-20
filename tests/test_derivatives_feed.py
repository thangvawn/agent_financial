from risk_dashboard.modules.market_portfolio.application import derivatives_feed


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_derivatives_feed_returns_all_standard_contracts_without_synthetic_values(monkeypatch, tmp_path):
    monkeypatch.setattr(derivatives_feed, "_CACHE_PATH", tmp_path / "derivatives.json")

    def fake_get(url, params, timeout, headers):
        if url == derivatives_feed._CONTRACTS_URL:
            return _Response({"total": 4, "data": [
                {"symbol": "VN30F2607", "type": "VN30F1M", "marketPrice": 1322, "basicPrice": 1320},
                {"symbol": "VN30F2608", "type": "VN30F2M", "marketPrice": 1322, "basicPrice": 1320},
                {"symbol": "VN30F2609", "type": "VN30F1Q", "marketPrice": 1322, "basicPrice": 1320},
                {"symbol": "VN30F2612", "type": "VN30F2Q", "marketPrice": 1322, "basicPrice": 1320},
            ]})
        assert params["symbol"] in {"VN30F2607", "VN30F2608", "VN30F2609", "VN30F2612"}
        return _Response([{"t": 1, "o": 1320, "h": 1325, "l": 1318, "c": 1322, "v": 1200}])

    monkeypatch.setattr(derivatives_feed.requests, "get", fake_get)
    payload = derivatives_feed.fetch_derivatives_snapshot(vn30_price=1320)

    assert payload["total"] == 4
    assert payload["freshness"] == "realtime"
    assert {item["symbol"] for item in payload["items"]} == {
        "VN30F1M", "VN30F2M", "VN30F1Q", "VN30F2Q"
    }
    assert all(item["price"] == 1322 for item in payload["items"])
    assert all(item["basis"] == 2 for item in payload["items"])
