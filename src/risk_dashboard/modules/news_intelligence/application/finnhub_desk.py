"""Finnhub-backed macro desk: economic calendar + compact quotes.

Designed for free tier (≈60 req/min): aggressive in-process caching, small symbol set,
single calendar window fetch per TTL. API key via FINNHUB_API_KEY env only.
"""

from __future__ import annotations

import os
import threading
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx

FINNHUB_BASE = "https://finnhub.io/api/v1"

# Cache TTLs — calendar changes slowly; quotes need snappier refresh but stay under rate limits.
_CALENDAR_TTL_SEC = 30 * 60
_QUOTES_TTL_SEC = 50

# Liquid US / global risk proxies; minimal call count per refresh.
_DEFAULT_QUOTE_SYMBOLS: tuple[str, ...] = (
    "SPY",
    "QQQ",
    "GLD",
    "BINANCE:BTCUSDT",
    "OANDA:EUR_USD",
)

_calendar_lock = threading.Lock()
_quotes_lock = threading.Lock()
_calendar_cache: dict[str, Any] = {"expires": 0.0, "payload": None, "error": None}
_quotes_cache: dict[str, Any] = {"expires": 0.0, "payload": None, "error": None}


def _api_key() -> str:
    return (os.environ.get("FINNHUB_API_KEY") or "").strip()


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


def datetime_now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _fetch_calendar(*, key: str, days: int = 14) -> dict[str, Any]:
    today = _utc_today()
    end = today + timedelta(days=max(1, min(days, 30)))
    params = {"from": today.isoformat(), "to": end.isoformat(), "token": key}
    with httpx.Client(timeout=8.0) as client:
        r = client.get(f"{FINNHUB_BASE}/calendar/economic", params=params)
        r.raise_for_status()
        data = r.json()
    events = data.get("economicCalendar") or []
    # Finnhub returns list of dicts; keep payload small for UI.
    trimmed: list[dict[str, Any]] = []
    for row in events[:80]:
        trimmed.append(
            {
                "date": row.get("date"),
                "time": row.get("time"),
                "country": row.get("country"),
                "event": row.get("event"),
                "impact": row.get("impact"),
                "estimate": row.get("estimate"),
                "actual": row.get("actual"),
                "prev": row.get("prev"),
                "unit": row.get("unit"),
            }
        )
    trimmed.sort(key=lambda r: (str(r.get("date") or ""), str(r.get("time") or "")))
    return {
        "from": params["from"],
        "to": params["to"],
        "event_count": len(trimmed),
        "events": trimmed,
    }


def _fetch_quote(client: httpx.Client, symbol: str, key: str) -> tuple[str, dict[str, Any] | None, str | None]:
    try:
        r = client.get(f"{FINNHUB_BASE}/quote", params={"symbol": symbol, "token": key})
        r.raise_for_status()
        j = r.json()
        if not j or j.get("c") in (0, None):
            return symbol, None, "no_data"
        return (
            symbol,
            {
                "c": j.get("c"),
                "d": j.get("d"),
                "dp": j.get("dp"),
                "h": j.get("h"),
                "l": j.get("l"),
                "o": j.get("o"),
                "pc": j.get("pc"),
                "t": j.get("t"),
            },
            None,
        )
    except Exception as exc:  # noqa: BLE001
        return symbol, None, str(exc)[:120]


def _fetch_all_quotes(*, key: str, symbols: tuple[str, ...]) -> dict[str, Any]:
    out: dict[str, dict[str, Any]] = {}
    errors: dict[str, str] = {}
    with httpx.Client(timeout=6.0) as client:
        for sym in symbols:
            sym_key, payload, err = _fetch_quote(client, sym, key)
            if payload is not None:
                out[sym_key] = payload
            elif err:
                errors[sym_key] = err
    return {"symbols": list(symbols), "quotes": out, "quote_errors": errors}


def get_finnhub_desk_snapshot(
    *,
    force: bool = False,
    calendar_days: int = 14,
    include_quotes: bool = False,
) -> dict[str, Any]:
    """Economic calendar from Finnhub; optional quote strip when include_quotes=True."""
    key = _api_key()
    now = time.monotonic()
    if not key:
        return {
            "enabled": False,
            "reason": "missing_api_key",
            "as_of": datetime_now_utc().isoformat(),
            "calendar": None,
            "quotes": None,
            "cache": {"calendar_ttl_sec": _CALENDAR_TTL_SEC, "quotes_ttl_sec": _QUOTES_TTL_SEC},
        }

    calendar_payload: dict[str, Any] | None = None
    calendar_err: str | None = None
    with _calendar_lock:
        if force or _calendar_cache["expires"] <= now or _calendar_cache["payload"] is None:
            try:
                _calendar_cache["payload"] = _fetch_calendar(key=key, days=calendar_days)
                _calendar_cache["error"] = None
            except Exception as exc:  # noqa: BLE001
                _calendar_cache["error"] = str(exc)[:200]
                # keep stale payload if any
            _calendar_cache["expires"] = now + _CALENDAR_TTL_SEC
        calendar_payload = _calendar_cache["payload"]
        calendar_err = _calendar_cache["error"]

    quotes_payload: dict[str, Any] | None = None
    quotes_err: str | None = None
    if include_quotes:
        with _quotes_lock:
            if force or _quotes_cache["expires"] <= now or _quotes_cache["payload"] is None:
                try:
                    _quotes_cache["payload"] = _fetch_all_quotes(key=key, symbols=_DEFAULT_QUOTE_SYMBOLS)
                    _quotes_cache["error"] = None
                except Exception as exc:  # noqa: BLE001
                    _quotes_cache["error"] = str(exc)[:200]
                _quotes_cache["expires"] = now + _QUOTES_TTL_SEC
            quotes_payload = _quotes_cache["payload"]
            quotes_err = _quotes_cache["error"]

    cache_block: dict[str, Any] = {
        "calendar_ttl_sec": _CALENDAR_TTL_SEC,
        "quotes_ttl_sec": _QUOTES_TTL_SEC,
    }
    if include_quotes:
        cache_block["quote_symbols"] = list(_DEFAULT_QUOTE_SYMBOLS)

    return {
        "enabled": True,
        "as_of": datetime_now_utc().isoformat(),
        "calendar": calendar_payload,
        "calendar_error": calendar_err,
        "quotes": quotes_payload,
        "quotes_error": quotes_err,
        "cache": cache_block,
    }
