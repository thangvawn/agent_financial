"""Live/fallback adapter for Vietnam index futures.

The market-portfolio endpoint must never manufacture quote values.  This adapter
uses DNSE's public OHLC endpoint at one-minute resolution and falls back to the
latest TCBS bar when the intraday endpoint is unavailable.  The response keeps
the provider/freshness metadata so consumers can distinguish realtime data from
an intentionally stale fallback.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import requests


CONTRACTS = (
    ("VN30F1M", "HĐTL VN30 tháng hiện tại"),
    ("VN30F2M", "HĐTL VN30 tháng kế tiếp"),
    ("VN30F1Q", "HĐTL VN30 quý gần nhất"),
    ("VN30F2Q", "HĐTL VN30 quý kế tiếp"),
)

_INTRADAY_URL = "https://services.entrade.com.vn/chart-api/v2/ohlcs/derivative"
_DAILY_URL = "https://apipubaws.tcbs.com.vn/futures-insight/v2/stock/bars-long-term"
_CONTRACTS_URL = "https://services.entrade.com.vn/entrade-api/derivatives"
_CACHE_PATH = Path(__file__).resolve().parents[4] / "data" / "vn_market" / "derivatives_snapshot.json"


def _number(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("data", "items", "result", "rows"):
            found = _items(payload.get(key))
            if found:
                return found
    return []


def _latest_bar(symbol: str, *, intraday: bool) -> dict[str, Any] | None:
    now = int(datetime.now(timezone.utc).timestamp())
    if intraday:
        url = _INTRADAY_URL
        params = {"from": now - 3 * 24 * 60 * 60, "to": now, "symbol": symbol, "resolution": "1"}
    else:
        url = _DAILY_URL
        params = {"ticker": symbol, "type": "derivative", "resolution": "D", "to": now, "countBack": 2}

    response = requests.get(url, params=params, timeout=8, headers={"Accept": "application/json"})
    response.raise_for_status()
    rows = _items(response.json())
    if not rows:
        return None
    row = rows[-1]
    # DNSE uses o/h/l/c/v/t; TCBS uses open/high/low/close/volume.
    return {
        "open": _number(row.get("open", row.get("o"))),
        "high": _number(row.get("high", row.get("h"))),
        "low": _number(row.get("low", row.get("l"))),
        "price": _number(row.get("close", row.get("c"))),
        "volume": _number(row.get("volume", row.get("v"))),
        "timestamp": row.get("t") or row.get("time") or row.get("tradingDate"),
    }


def _discover_contracts() -> dict[str, dict[str, Any]]:
    """Resolve display types to the exchange symbols currently being traded."""
    response = requests.get(_CONTRACTS_URL, timeout=8, headers={"Accept": "application/json"})
    response.raise_for_status()
    return {
        str(row.get("type")): row
        for row in _items(response.json())
        if row.get("type") and row.get("symbol")
    }


def _load_cache() -> dict[str, Any] | None:
    try:
        return json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _save_cache(payload: dict[str, Any]) -> None:
    try:
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_PATH.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def fetch_derivatives_snapshot(vn30_price: float | None = None) -> dict[str, Any]:
    """Return all four standard VN30 futures, with real quote values when available."""
    previous = _load_cache()
    source = "dnse_1m"
    stale = False
    errors: list[str] = []
    items: list[dict[str, Any]] = []

    discovered: dict[str, dict[str, Any]] = {}
    try:
        discovered = _discover_contracts()
        source = "entrade_derivatives"
    except Exception as exc:
        errors.append(f"contracts: {type(exc).__name__}")

    for contract_type, name in CONTRACTS:
        contract = discovered.get(contract_type, {})
        symbol = str(contract.get("symbol") or contract_type)
        bar = None
        try:
            bar = _latest_bar(symbol, intraday=True)
        except Exception as exc:
            errors.append(f"{symbol}: {type(exc).__name__}")
        if bar is None:
            try:
                bar = _latest_bar(symbol, intraday=False)
                source = "tcbs_latest_bar"
            except Exception as exc:
                errors.append(f"{symbol}: {type(exc).__name__}")

        old = next((x for x in (previous or {}).get("items", []) if x.get("type") == contract_type or x.get("symbol") == symbol), None)
        base_quote = {
            "price": contract.get("marketPrice"),
            "ref": contract.get("basicPrice"),
            "ceil": contract.get("ceilingPrice"),
            "floor": contract.get("floorPrice"),
            "timestamp": contract.get("modifiedDate"),
        }
        quote = bar or (base_quote if any(value is not None for value in base_quote.values()) else old) or {}
        price = _number(quote.get("price"))
        previous_close = _number(quote.get("previous_close", quote.get("ref")))
        change = _number(quote.get("change"))
        if change is None and price is not None and previous_close is not None:
            change = price - previous_close
        change_pct = _number(quote.get("change_pct"))
        if change_pct is None and change is not None and previous_close:
            change_pct = change / previous_close * 100
        items.append({
            "symbol": contract_type,
            "exchange_symbol": symbol,
            "type": contract_type,
            "name": name,
            "price": price,
            "change": change,
            "change_pct": change_pct,
            "basis": price - vn30_price if price is not None and vn30_price is not None else None,
            "volume": int(quote["volume"]) if _number(quote.get("volume")) is not None else None,
            "open_interest": _number(quote.get("open_interest", quote.get("oi"))),
            "ceil": _number(quote.get("ceil")),
            "floor": _number(quote.get("floor")),
            "ref": previous_close,
            "open": _number(quote.get("open")),
            "high": _number(quote.get("high")),
            "low": _number(quote.get("low")),
            "quote_time": quote.get("timestamp"),
        })

    has_quotes = any(item.get("price") is not None for item in items)
    if not has_quotes:
        if previous:
            stale = True
            source = f"cache:{previous.get('source', 'unknown')}"
        else:
            source = "unavailable"
    payload = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "total": len(items),
        "source": source,
        "freshness": "unavailable" if not has_quotes else ("stale" if stale else ("realtime" if source == "dnse_1m" else "near_realtime")),
        "stale": stale,
        "errors": errors[:8],
        "items": items,
    }
    if any(item.get("price") is not None for item in items):
        _save_cache(payload)
    return payload
