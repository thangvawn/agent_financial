from __future__ import annotations

from risk_dashboard.modules.data_hub.application.vn_market_feed import VnMarketFeedProducer

_vn = VnMarketFeedProducer()


def quote_last_price(symbol: str) -> float | None:
    """Best-effort last price from VN market snapshot (educational mock fill)."""
    needle = symbol.strip().upper()
    payload = _vn.snapshot()
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
    payload = _vn.snapshot()
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
