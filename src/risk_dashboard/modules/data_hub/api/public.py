from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query

from risk_dashboard.modules.data_hub.application.services import DataHubService
from risk_dashboard.modules.data_hub.application.stock_screener import (
    ScreenerQueryError,
    StockScreenerService,
)
from risk_dashboard.modules.data_hub.application.vn_market_feed import VnMarketFeedProducer
from risk_dashboard.modules.data_hub.domain.market_heatmap import heatmap_items
from risk_dashboard.modules.data_hub.infrastructure.vn_industries import VnIndustryCatalog

router = APIRouter(prefix="/data-hub", tags=["DataHub"])

_vn_market = VnMarketFeedProducer()
_industries = VnIndustryCatalog(_vn_market.cache_dir)
_screener = StockScreenerService()


@router.get("/vn-market/heatmap")
def get_vn_heatmap() -> dict:
    # One snapshot for the whole map; no mixed pages or provider requests.
    payload = _vn_market.snapshot(read_only=True)
    quotes, _, classification = _industries.enrich(payload.get("items") or [])
    items = heatmap_items(quotes)
    last_success = payload.get("last_success_at") or payload.get("as_of")
    market_open = _is_vn_market_hours()
    return {
        "items": items,
        "total": len(items),
        "as_of": payload.get("as_of"),
        "last_success_at": last_success,
        "age_seconds": _age_seconds(last_success),
        "source": payload.get("source"),
        "freshness": payload.get("freshness", "degraded"),
        "stale_reason": payload.get("stale_reason"),
        "industry_coverage": classification,
        "market_session": "open" if market_open else "closed",
        "refresh_interval_seconds": 30 if market_open else 300,
        "units": {"price": "VND", "value": "VND", "market_cap": "billion VND", "volume": "shares"},
    }


@router.get("/vn-market/screener")
def get_vn_screener(
    preset: str = Query("", max_length=40),
    technical: str = Query("all", max_length=40),
    sector: str = Query("", max_length=100),
    exchange: str = Query("", pattern="^(|HOSE|HSX|HNX|UPCOM)$"),
    sort: str = Query("score_desc", max_length=40),
    limit: int = Query(50, ge=1, le=100),
    cursor: str = Query("", max_length=512),
    snapshot_id: str = Query("", pattern="^([a-f0-9]{24})?$"),
) -> dict:
    # Read the cached universe. A click never performs 1,500 provider requests.
    quotes = _vn_market._load_json(_vn_market.snapshot_path).get("items", [])
    try:
        return _screener.query(
            quotes, preset=preset, technical=technical, sector=sector,
            exchange=exchange, sort=sort, limit=limit, cursor=cursor,
            snapshot_id=snapshot_id,
        )
    except ScreenerQueryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


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
def get_global_terminal(
    view: str = "dashboard",
    refresh: bool = Query(
        False, description="Force one provider refresh for an explicit user action."
    ),
) -> dict:
    return DataHubService().get_global_terminal(view=view, force_refresh=refresh)


@router.get("/instruments/{symbol}/history")
def get_instrument_history(
    symbol: str,
    period: str = "6mo",
    interval: str = "1d",
    refresh: bool = False,
) -> dict:
    return DataHubService().get_instrument_history(symbol=symbol, period=period, interval=interval, force_refresh=refresh)


@router.get("/vn-market/universe")
def get_vn_universe() -> dict:
    """List of Vietnamese equities tracked (HOSE + HNX + UPCOM)."""
    return _vn_market.universe()


@router.get("/vn-market/snapshot")
def get_vn_snapshot(
    sort: str = Query(
        "market_cap_desc",
        pattern="^(market_cap_desc|change_desc|change_asc|volume_desc|value_desc|"
        "foreign_net_buy_desc|symbol_asc)$",
    ),
    exchange: str | None = Query(None, pattern="^(HOSE|HSX|HNX|UPCOM)$"),
    search: str | None = Query(None, max_length=12),
    industry: str | None = Query(None, pattern=r"^(\d{4}|unclassified)$"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0, le=100000),
    refresh: bool = Query(False, description="Request a non-blocking provider refresh."),
) -> dict:
    if refresh:
        # Do not make an interactive browser request wait on vnstock. The
        # current cache is returned immediately and the next poll observes
        # the newly written snapshot if the provider succeeds.
        _vn_market.refresh_in_background()
    payload = _vn_market.snapshot()
    items = payload.get("items", []) or []
    universe_total = len(items)
    items, industry_options, industry_coverage = _industries.enrich(items)
    if (
        industry and industry != "unclassified"
        and industry not in _industries.read().get("industries", {})
    ):
        raise HTTPException(status_code=422, detail="Nhóm ngành không hợp lệ.")

    def _number(value) -> float | None:
        try:
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None

    market_summary: dict[str, dict] = {}
    for market in ("HSX", "HNX", "UPCOM"):
        market_items = [
            item for item in items
            if (
                "HSX" if (item.get("exchange") or "").upper() == "HOSE"
                else (item.get("exchange") or "").upper()
            ) == market
        ]
        changes = [_number(item.get("change_pct")) for item in market_items]
        changes = [value for value in changes if value is not None]
        traded_value_vnd = sum(
            value for value in (_number(item.get("value")) for item in market_items)
            if value is not None
        )
        market_summary[market] = {
            "exchange": market,
            "advances": sum(value > 0 for value in changes),
            "unchanged": sum(value == 0 for value in changes),
            "declines": sum(value < 0 for value in changes),
            "quoted": len(changes),
            "turnover_billion": round(traded_value_vnd / 1_000_000_000, 1),
        }

    if exchange:
        norm = "HSX" if exchange == "HOSE" else exchange
        items = [
            i for i in items
            if (i.get("exchange") or "").upper().replace("HOSE", "HSX") == norm
        ]

    if search:
        needle = search.strip().upper()
        items = [
            i for i in items
            if needle in (i.get("symbol") or "").upper() or needle in (i.get("name") or "").upper()
        ]

    if industry:
        wanted = None if industry == 'unclassified' else industry
        items = [item for item in items if item.get('industry_code') == wanted]

    def _safe(v, default=0):
        return v if v is not None else default

    items = sorted(items, key=lambda row: row.get('symbol') or '')

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

    last_success_at = payload.get("last_success_at") or payload.get("as_of")
    age_seconds = _age_seconds(last_success_at)
    in_market_hours = _is_vn_market_hours()
    refresh_interval = max(
        int(os.getenv("VN_MARKET_INTERVAL_FAST_SEC", "12")) if in_market_hours
        else int(os.getenv("VN_MARKET_INTERVAL_SLOW_SEC", "300")),
        5 if in_market_hours else 60,
    )
    return {
        "as_of": payload.get("as_of"),
        "last_success_at": last_success_at,
        "age_seconds": age_seconds,
        "source": payload.get("source"),
        "freshness": payload.get("freshness"),
        "stale_reason": payload.get("stale_reason"),
        "market_session": "open" if in_market_hours else "closed",
        "refresh_interval_seconds": refresh_interval,
        "refresh_requested": refresh,
        "total": len(items),
        "universe_total": universe_total,
        "returned": len(items[offset:offset + limit]),
        "offset": offset,
        "next_offset": offset + limit if offset + limit < len(items) else None,
        "industry_options": industry_options,
        "industry_coverage": industry_coverage,
        "market_summary": market_summary,
        "items": items[offset:offset + limit],
    }


def _age_seconds(value: object) -> int | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return max(0, int((datetime.now(timezone.utc) - parsed).total_seconds()))
    except (TypeError, ValueError, OverflowError):
        return None


def _is_vn_market_hours() -> bool:
    """Return the scheduler's broad weekday warm-up/trading window in ICT."""
    now = datetime.now(timezone.utc) + timedelta(hours=7)
    if now.weekday() >= 5:
        return False
    opening = now.replace(hour=8, minute=50, second=0, microsecond=0)
    closing = now.replace(hour=15, minute=10, second=0, microsecond=0)
    return opening <= now <= closing
