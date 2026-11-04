"""Quote provenance and conservative freshness, independent of cache write time."""

import math
from datetime import datetime, timezone


def finite_number(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def timestamp(value):
    if not value:
        return None
    try:
        stamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return (
            stamp.replace(tzinfo=timezone.utc)
            if stamp.tzinfo is None
            else stamp.astimezone(timezone.utc)
        )
    except (TypeError, ValueError, OverflowError):
        return None


def quote_health(row, *, fallback_fetched_at=None, max_fetch_age=75, now=None):
    now = now or datetime.now(timezone.utc)
    price = finite_number(row.get("price"))
    quote_at = timestamp(row.get("updated_at") or row.get("quote_at"))
    fetched_at = timestamp(row.get("fetched_at") or fallback_fetched_at)
    quote_age = (now - quote_at).total_seconds() if quote_at else None
    fetch_age = (now - fetched_at).total_seconds() if fetched_at else None
    # A closed market can legitimately have an old quote. Preserve and label it;
    # a recent fetch must never turn that old quote into a newly traded price.
    max_quote_age = 300 if row.get("group") == "crypto" else 1200
    if price is None:
        reason = "quote_unavailable"
    elif quote_age is None or quote_age < -60:
        reason = "quote_time_unknown"
    elif row.get("refresh_failed"):
        reason = "provider_refresh_failed"
    elif quote_age > max_quote_age:
        reason = "quote_age_exceeded"
    elif fetch_age is None or fetch_age < -60 or fetch_age > max_fetch_age:
        reason = "cache_age_exceeded"
    else:
        reason = None
    status = "unavailable" if price is None else "stale" if reason else "available"
    return {
        **row,
        "price": price,
        "change": finite_number(row.get("change")) if price is not None else None,
        "change_pct": finite_number(row.get("change_pct")) if price is not None else None,
        "updated_at": quote_at.isoformat() if quote_at else None,
        "quote_at": quote_at.isoformat() if quote_at else None,
        "fetched_at": fetched_at.isoformat() if fetched_at else None,
        "quote_age_seconds": max(0, quote_age) if quote_age is not None else None,
        "quote_status": status,
        "freshness": "fresh"
        if status == "available"
        else "stale"
        if price is not None
        else "degraded",
        "stale_reason": reason,
    }


def quote_summary(items, *, expected=None):
    quoted = sum(row.get("price") is not None for row in items)
    available = sum(row.get("quote_status") == "available" for row in items)
    total = expected if expected is not None else len(items)
    times = [
        row["updated_at"] for row in items if row.get("updated_at") and row.get("price") is not None
    ]
    return {
        "as_of": max(times) if times else None,
        "oldest_quote_at": min(times) if times else None,
        "freshness": "degraded"
        if quoted < total or not quoted
        else "fresh"
        if available == total
        else "stale",
        "coverage": {
            "expected": total,
            "quoted": quoted,
            "available": available,
            "stale": quoted - available,
            "unavailable": total - quoted,
        },
    }
