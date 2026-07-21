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
    sort: str = Query("market_cap_desc", pattern="^(market_cap_desc|change_desc|change_asc|volume_desc|value_desc|foreign_net_buy_desc|symbol_asc)$"),
    exchange: str | None = Query(None, pattern="^(HOSE|HSX|HNX|UPCOM)$"),
    search: str | None = Query(None, max_length=12),
    limit: int = Query(50, ge=1, le=500),
) -> dict:
    payload = _vn_market.snapshot()
    items = payload.get("items", []) or []

    def _number(value) -> float | None:
        try:
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None

    market_summary: dict[str, dict] = {}
    for market in ("HSX", "HNX", "UPCOM"):
        market_items = [
            item for item in items
            if ("HSX" if (item.get("exchange") or "").upper() == "HOSE" else (item.get("exchange") or "").upper()) == market
        ]
        changes = [_number(item.get("change_pct")) for item in market_items]
        changes = [value for value in changes if value is not None]
        traded_value_million = sum(
            value for value in (_number(item.get("value")) for item in market_items)
            if value is not None
        )
        market_summary[market] = {
            "exchange": market,
            "advances": sum(value > 0 for value in changes),
            "unchanged": sum(value == 0 for value in changes),
            "declines": sum(value < 0 for value in changes),
            "quoted": len(changes),
            "turnover_billion": round(traded_value_million / 1000, 1),
        }

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

    if sort == "market_cap_desc":
        items = sorted(items, key=lambda x: _safe(x.get("market_cap"), -1), reverse=True)
    elif sort == "change_desc":
        items = sorted(items, key=lambda x: _safe(x.get("change_pct"), -1e9), reverse=True)
    elif sort == "change_asc":
        items = sorted(items, key=lambda x: _safe(x.get("change_pct"), 1e9))
    elif sort == "volume_desc":
        items = sorted(items, key=lambda x: _safe(x.get("volume")), reverse=True)
    elif sort == "value_desc":
        items = sorted(items, key=lambda x: _safe(x.get("value")), reverse=True)
    elif sort == "foreign_net_buy_desc":
        items = sorted(
            items,
            key=lambda x: _safe(x.get("foreign_net_buy")),
            reverse=True,
        )
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
        "market_summary": market_summary,
        "items": items[:limit],
    }
