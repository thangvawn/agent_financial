"""Watchlist quotes across assets, without changing VND paper-trading prices.

Read the snapshots maintained by the market schedulers. A missing provider must
not block the other asset classes or manufacture a price for a saved symbol.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any

from risk_dashboard.modules.data_hub.application.global_market_feed import (
    GLOBAL_MARKET_INSTRUMENTS,
    GlobalMarketFeedProducer,
)
from risk_dashboard.modules.data_hub.application.vn_market_feed import VnMarketFeedProducer
from risk_dashboard.modules.market_portfolio.application.derivatives_feed import (
    CONTRACTS,
    _load_cache,
)

_vn = VnMarketFeedProducer()
_global = GlobalMarketFeedProducer()
_ALIASES = {i.yahoo_symbol.upper(): i.symbol for i in GLOBAL_MARKET_INSTRUMENTS if i.yahoo_symbol}
_ALIASES.update({i.name.upper(): i.symbol for i in GLOBAL_MARKET_INSTRUMENTS if i.group == "fx"})
_ALIASES.update(
    {f"{i.symbol}/USD": i.symbol for i in GLOBAL_MARKET_INSTRUMENTS if i.group == "crypto"}
)
_ALIASES.update({"HNX": "HNXINDEX", "UPCOM": "UPCOMINDEX"})


def normalize_watchlist_symbol(symbol: str) -> str:
    value = symbol.strip().upper()
    return _ALIASES.get(value, value)


def _number(value: Any) -> float | None:
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (ValueError, TypeError):
        return None


def _quote(item: dict, group: str, feed: dict) -> dict:
    symbol = item["symbol"]
    price = _number(item.get("price"))
    if price is None or price <= 0:
        price = None
    updated_at = item.get("updated_at") or feed.get("as_of")
    # A quote's timestamp takes precedence over the mixed-feed snapshot time.
    ttl = 1200 if group in {"indices", "fx", "commodities"} else 300
    stale = True
    if updated_at:
        try:
            stamp = datetime.fromisoformat(str(updated_at).replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=timezone.utc)
            updated_at = stamp.isoformat()
            stale = (datetime.now(timezone.utc) - stamp).total_seconds() > ttl
        except (ValueError, TypeError):
            pass
    unit = item.get("unit")
    if not unit:
        unit = "VND" if group == "vn_stocks" else "USD" if group == "crypto" else "điểm"
        if group == "fx" and symbol != "DXY":
            unit = f"{symbol[3:]} / {symbol[:3]}"
    return {
        "symbol": symbol,
        "name": item.get("name") or symbol,
        "asset_class": group,
        "exchange": item.get("exchange") or "",
        "unit": unit,
        "price": price,
        "change": _number(item.get("change")) if price is not None else None,
        "change_pct": _number(item.get("change_pct")) if price is not None else None,
        "market_cap": _number(item.get("market_cap")),
        "market_cap_unit": "tỷ VND" if group == "vn_stocks" else "USD" if group == "crypto" else "",
        "volume": _number(item.get("volume", item.get("volume_24h"))),
        "source": item.get("source") or feed.get("source"),
        "updated_at": updated_at,
        "quote_status": "unavailable" if price is None else "stale" if stale else "available",
    }


def watchlist_instruments() -> list[dict[str, Any]]:
    catalog: dict[str, dict] = {}
    try:
        vn = _vn.snapshot(read_only=True)
    except (OSError, ValueError, KeyError, TypeError):
        vn = {}
    try:
        universe = json.loads(_vn.universe_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        universe = {}
    for item in [*(universe.get("tickers") or []), *(vn.get("items") or [])]:
        if item.get("symbol"):
            catalog[item["symbol"]] = _quote(item, "vn_stocks", vn)

    try:
        feed = _global.snapshot(read_only=True)
    except (OSError, ValueError, KeyError, TypeError):
        feed = {}
    global_items = {
        item["symbol"]: item
        for items in feed.get("groups", {}).values()
        for item in items
        if item.get("symbol")
    }
    for instrument in GLOBAL_MARKET_INSTRUMENTS:
        item = {"symbol": instrument.symbol, "name": instrument.name, "unit": instrument.unit}
        item.update(global_items.get(instrument.symbol, {}))
        catalog[instrument.symbol] = _quote(item, instrument.group, feed)

    derivatives = _load_cache() or {}
    derivative_items = {
        item["symbol"]: item for item in derivatives.get("items", []) if item.get("symbol")
    }
    for symbol, name in CONTRACTS:
        item = {"symbol": symbol, "name": name, **derivative_items.get(symbol, {})}
        catalog[symbol] = _quote(item, "derivatives", derivatives)
    return list(catalog.values())


def quote_details_map(symbols: list[str]) -> dict[str, dict[str, Any]]:
    if not symbols:
        return {}
    catalog = {item["symbol"]: item for item in watchlist_instruments()}
    return {
        symbol: catalog[canonical]
        for symbol in symbols
        if (canonical := normalize_watchlist_symbol(symbol)) in catalog
    }
