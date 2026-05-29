from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from risk_dashboard.modules.data_hub.application.services import DataHubService
from risk_dashboard.modules.data_hub.application.vn_market_feed import VnMarketFeedProducer

router = APIRouter(prefix="/data-hub", tags=["DataHub"])

_vn_market = VnMarketFeedProducer()


@router.get("/topics")
def list_data_hub_topics() -> dict:
    return DataHubService().list_topic_status()


@router.get("/topics/{topic:path}")
def get_data_hub_topic(topic: str) -> dict:
    snapshot = DataHubService().get_topic(topic)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Unknown data hub topic.")
    return snapshot.to_dict()


@router.get("/global-terminal")
def get_global_terminal(view: str = "dashboard") -> dict:
    return DataHubService().get_global_terminal(view=view)


@router.get("/instruments/{symbol}/history")
def get_instrument_history(
    symbol: str,
    period: str = "6mo",
    interval: str = "1d",
) -> dict:
    return DataHubService().get_instrument_history(symbol=symbol, period=period, interval=interval)


@router.get("/vn-market/universe")
def get_vn_universe() -> dict:
    """List of Vietnamese equities tracked (HOSE + HNX + UPCOM)."""
    return _vn_market.universe()


@router.get("/vn-market/snapshot")
def get_vn_snapshot(
    sort: str = Query("change_desc", pattern="^(change_desc|change_asc|volume_desc|value_desc|symbol_asc)$"),
    exchange: str | None = Query(None, pattern="^(HOSE|HSX|HNX|UPCOM)$"),
    search: str | None = Query(None, max_length=12),
    limit: int = Query(50, ge=1, le=500),
) -> dict:
    payload = _vn_market.snapshot()
    items = payload.get("items", []) or []

    if exchange:
        norm = "HSX" if exchange == "HOSE" else exchange
        items = [i for i in items if (i.get("exchange") or "").upper() == norm]

    if search:
        needle = search.strip().upper()
        items = [
            i for i in items
            if needle in (i.get("symbol") or "").upper() or needle in (i.get("name") or "").upper()
        ]

    def _safe(v, default=0):
        return v if v is not None else default

    if sort == "change_desc":
        items = sorted(items, key=lambda x: _safe(x.get("change_pct"), -1e9), reverse=True)
    elif sort == "change_asc":
        items = sorted(items, key=lambda x: _safe(x.get("change_pct"), 1e9))
    elif sort == "volume_desc":
        items = sorted(items, key=lambda x: _safe(x.get("volume")), reverse=True)
    elif sort == "value_desc":
        items = sorted(items, key=lambda x: _safe(x.get("value")), reverse=True)
    else:
        items = sorted(items, key=lambda x: (x.get("symbol") or ""))

    # Exact symbol matches float to the top when searching, regardless of sort.
    if search:
        needle = search.strip().upper()
        items.sort(key=lambda x: 0 if (x.get("symbol") or "").upper() == needle else 1)

    return {
        "as_of": payload.get("as_of"),
        "source": payload.get("source"),
        "freshness": payload.get("freshness"),
        "total": payload.get("count", len(payload.get("items", []) or [])),
        "returned": min(limit, len(items)),
        "items": items[:limit],
    }

