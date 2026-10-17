from __future__ import annotations

from risk_dashboard.modules.data_hub.application.vn_market_feed import VnMarketFeedProducer

_vn = VnMarketFeedProducer()


def quote_last_price(symbol: str) -> float | None:
    """Best-effort last price from VN market snapshot (educational mock fill)."""
    needle = symbol.strip().upper()
    try:
        payload = _vn.snapshot()
    except (ConnectionError, TimeoutError, OSError, ValueError, KeyError):
        return None
    for item in payload.get("items") or []:
        if (item.get("symbol") or "").upper() == needle:
            price = item.get("price")
            if price is None:
                price = item.get("last") or item.get("close")
            try:
                value = float(price)
            except (TypeError, ValueError):
                return None
            return value if value > 0 else None
    return None


def quote_map(symbols: list[str]) -> dict[str, float]:
    wanted = {s.strip().upper() for s in symbols if s}
    if not wanted:
        return {}
    try:
        payload = _vn.snapshot()
    except (ConnectionError, TimeoutError, OSError, ValueError, KeyError):
        return {}

    out: dict[str, float] = {}
    for item in payload.get("items") or []:
        sym = (item.get("symbol") or "").upper()
        if sym not in wanted:
            continue
        price = item.get("price")
        if price is None:
            price = item.get("last") or item.get("close")
        try:
            value = float(price)
        except (TypeError, ValueError):
            continue
        if value > 0:
            out[sym] = value
    return out


def quote_details_map(symbols: list[str]) -> dict[str, dict[str, Any]]:
    wanted = {s.strip().upper() for s in symbols if s}
    if not wanted:
        return {}
    try:
        payload = _vn.snapshot()
    except (ConnectionError, TimeoutError, OSError, ValueError, KeyError):
        return {}

    out: dict[str, dict[str, Any]] = {}
    for item in payload.get("items") or []:
        sym = (item.get("symbol") or "").upper()
        if sym not in wanted:
            continue
        price = item.get("price")
        if price is None:
            price = item.get("last") or item.get("close")
        try:
            value = float(price) if price is not None else None
        except (TypeError, ValueError):
            value = None

        out[sym] = {
            "symbol": sym,
            "name": item.get("name") or "",
            "exchange": item.get("exchange") or "",
            "price": value if (value is not None and value > 0) else None,
            "change": item.get("change"),
            "change_pct": item.get("change_pct"),
            "market_cap": item.get("market_cap"),
            "volume": item.get("volume"),
            "ref_price": item.get("ref_price"),
            "ceiling": item.get("ceiling"),
            "floor": item.get("floor"),
            "high": item.get("high"),
            "low": item.get("low"),
        }
    return out

