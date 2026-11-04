from copy import deepcopy

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from risk_dashboard.modules.data_hub.api import public


@pytest.fixture
def client(monkeypatch):
    # Actual quote shape: SSI does not include any industry field.
    quotes = [
        {"symbol": "VIC", "exchange": "HOSE", "market_cap": 900, "volume": 50},
        {"symbol": "VCB", "exchange": "HOSE", "market_cap": 500, "volume": 200},
        {"symbol": "MBB", "exchange": "HOSE", "market_cap": 300, "volume": 400},
        {"symbol": "ACB", "exchange": "HNX", "market_cap": 100, "volume": 100},
        {"symbol": "ZZTEST", "exchange": "HOSE", "market_cap": 1, "volume": 1},
    ]
    monkeypatch.setattr(
        public._vn_market, "snapshot", lambda: {"items": deepcopy(quotes), "count": 5}
    )
    app = FastAPI()
    app.include_router(public.router)
    with TestClient(app) as test_client:
        yield test_client


def test_industry_filter_enriches_real_quote_shape_before_pagination(client):
    response = client.get("/data-hub/vn-market/snapshot", params={"industry": "8350", "limit": 1})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["universe_total"] == 5
    assert [x["symbol"] for x in body["items"]] == ["VCB"]
    second = client.get(
        "/data-hub/vn-market/snapshot", params={"industry": "8350", "limit": 1, "offset": 1}
    ).json()
    assert [x["symbol"] for x in second["items"]] == ["MBB"]
    assert second["total"] == 3


def test_industry_and_exchange_intersect_and_sort_on_current_quotes(client):
    body = client.get(
        "/data-hub/vn-market/snapshot",
        params={"industry": "8350", "exchange": "HSX", "sort": "volume_desc"},
    ).json()
    assert [x["symbol"] for x in body["items"]] == ["MBB", "VCB"]
    assert body["total"] == 2
    assert all(x["industry_code"] == "8350" for x in body["items"])
    assert client.get("/data-hub/vn-market/snapshot").json()["total"] == 5


def test_unknown_symbols_are_explicit_and_catalog_matches_data(client):
    body = client.get("/data-hub/vn-market/snapshot", params={"industry": "unclassified"}).json()
    assert [x["symbol"] for x in body["items"]] == ["ZZTEST"]
    assert body["industry_coverage"]["unclassified"] == 1
    options = {o["code"]: o for o in body["industry_options"]}
    assert options["8350"]["count"] == 3 and options["8350"]["name"] == "Ngân hàng"
    for bad in ["Ngân hàng", "../data", "1234"]:
        assert (
            client.get("/data-hub/vn-market/snapshot", params={"industry": bad}).status_code == 422
        )


def test_classification_outage_keeps_last_good_catalog(tmp_path, monkeypatch):
    import json

    from risk_dashboard.modules.data_hub.infrastructure.vn_industries import SEED, VnIndustryCatalog

    saved = json.loads(SEED.read_text())
    saved["retrieved_at"] = "2000-01-01T00:00:00+00:00"
    catalog = VnIndustryCatalog(tmp_path)
    catalog.store.write("industries.json", saved)
    monkeypatch.setattr(
        "risk_dashboard.modules.data_hub.infrastructure.vn_industries.requests.get",
        lambda *a, **kw: (_ for _ in ()).throw(ValueError("invalid response")),
    )
    assert catalog.refresh() == saved
    assert catalog.read() == saved


def test_catalog_is_pointed_to_real_icb_codes_and_does_not_guess_names(tmp_path):
    from risk_dashboard.modules.data_hub.infrastructure.vn_industries import VnIndustryCatalog

    rows, options, coverage = VnIndustryCatalog(tmp_path).enrich(
        [{"symbol": "VCB"}, {"symbol": "FPT"}, {"symbol": "ZZTEST", "name": "Ngân hàng giả"}]
    )
    assert [x["industry_code"] for x in rows] == ["8350", "9530", None]
    assert coverage["classified"] == 2 and coverage["unclassified"] == 1


def test_provider_classification_keeps_alphanumeric_stock_symbols(tmp_path):
    from risk_dashboard.modules.data_hub.infrastructure.vn_industries import (
        VnIndustryCatalog,
        parse_classification,
    )

    parsed = parse_classification(
        {"data": [{"code": "D2D", "icbLv3": {"code": "8630", "name": "Bất động sản"}}]}
    )
    assert parsed["symbols"]["D2D"] == "8630"
    rows, _, _ = VnIndustryCatalog(tmp_path).enrich([{"symbol": "D2D"}])
    assert rows[0]["industry_code"] == "8630"


def test_invalid_cache_falls_back_to_verified_bundle(tmp_path):
    from risk_dashboard.modules.data_hub.infrastructure.vn_industries import VnIndustryCatalog

    catalog = VnIndustryCatalog(tmp_path)
    payload = catalog.read()
    payload["symbols"]["VCB"] = ["invalid-code"]
    catalog.store.write("industries.json", payload)
    assert catalog.read()["symbols"]["VCB"] == "8350"
