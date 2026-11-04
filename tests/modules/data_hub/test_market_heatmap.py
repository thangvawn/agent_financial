from copy import deepcopy

from fastapi import FastAPI
from fastapi.testclient import TestClient

from risk_dashboard.modules.data_hub.api import public
from risk_dashboard.modules.data_hub.domain.market_heatmap import heatmap_items


def test_heatmap_uses_one_read_only_snapshot_and_entire_universe(monkeypatch):
    rows = [
        {"symbol": f"X{i:04d}", "price": 10000, "change_pct": 1, "value": 1000000}
        for i in range(1521)
    ]
    calls = []

    def snapshot(*, read_only=False):
        calls.append(read_only)
        return {
            "items": deepcopy(rows),
            "as_of": "2026-11-02T07:00:00Z",
            "source": "fixture",
            "freshness": "stale",
        }

    monkeypatch.setattr(public._vn_market, "snapshot", snapshot)
    app = FastAPI()
    app.include_router(public.router)
    response = TestClient(app).get("/data-hub/vn-market/heatmap")
    assert response.status_code == 200
    data = response.json()
    assert calls == [True]
    assert data["total"] == len(data["items"]) == 1521
    assert data["freshness"] == "stale"
    assert data["units"]["value"] == "VND"
    assert all(r["market_cap"] is None and r["sector_id"] == "unknown" for r in data["items"])


def test_known_icb_sectors_not_guessed_from_company_names():
    rows = heatmap_items(
        [
            {"symbol": "VIC", "industry_code": "8630", "exchange": "HSX"},
            {"symbol": "VCB", "industry_code": "8350", "exchange": "HOSE"},
            {"symbol": "FPT", "industry_code": "9530"},
            {"symbol": "XXX", "name": "Ngân hàng tự đặt"},
        ]
    )
    data = {r["symbol"]: r for r in rows}
    assert data["VIC"]["sector_id"] == "real_estate" and data["VIC"]["exchange"] == "HOSE"
    assert data["VCB"]["sector"] == "Tài chính"
    assert data["FPT"]["sector"] == "Công nghệ"
    assert data["XXX"]["sector_id"] == "unknown"


def test_overview_turnover_uses_same_vnd_unit_as_heatmap(monkeypatch):
    payload = {
        "items": [
            {"symbol": "FPT", "exchange": "HOSE", "value": 2_500_000_000},
            {"symbol": "VCB", "exchange": "HSX", "value": 500_000_000},
            {"symbol": "SHS", "exchange": "HNX", "value": 800_000_000},
        ],
        "freshness": "stale",
    }
    monkeypatch.setattr(public._vn_market, "snapshot", lambda **kwargs: deepcopy(payload))
    app = FastAPI()
    app.include_router(public.router)
    client = TestClient(app)
    summary = client.get("/data-hub/vn-market/snapshot").json()["market_summary"]
    assert summary["HSX"]["turnover_billion"] == 3.0
    assert summary["HNX"]["turnover_billion"] == 0.8
    heatmap = client.get("/data-hub/vn-market/heatmap").json()
    assert sum(row["value"] for row in heatmap["items"]) / 1e9 == 3.8


def test_bad_numbers_zero_and_missing_are_not_fabricated():
    rows = heatmap_items(
        [
            {
                "symbol": "FPT",
                "price": float("nan"),
                "value": float("inf"),
                "market_cap": -1,
                "volume": 0,
                "change_pct": None,
            },
            {"symbol": "<script>", "value": 123},
            {"symbol": "D2D", "price": True, "value": "", "change_pct": "-2.5"},
        ]
    )
    assert len(rows) == 2
    fpt = next(r for r in rows if r["symbol"] == "FPT")
    assert fpt["price"] is None and fpt["value"] is None and fpt["market_cap"] is None
    assert fpt["volume"] == 0 and fpt["change_pct"] is None
    assert rows[0]["change_pct"] == -2.5 and rows[0]["price"] is None
