"""Commodity catalog, quote provenance and idempotent storage of provider prices."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from risk_dashboard.modules.data_hub.application import global_market_feed as market_feed
from risk_dashboard.modules.data_hub.application.global_market_feed import GlobalMarketFeedProducer
from risk_dashboard.modules.data_hub.application.quote_quality import (
    finite_number,
    quote_health,
    quote_summary,
)
from risk_dashboard.platform.database.connection import open_db


def _stored_quotes(conn):
    # Older rows used the global fetch timestamp as as_of. Rank their actual
    # provider timestamps instead, so a falsely recent legacy row cannot shadow
    # a correctly timestamped quote written by this version.
    rows = conn.execute("""
        SELECT i.symbol, i.name, i.provider_symbol AS yahoo_symbol, i.category,
               i.unit, q.as_of, q.price, q.change, q.change_pct, q.high_24h,
               q.low_24h, q.volume_24h, q.source, q.raw_json
        FROM commodity_instruments i JOIN commodity_quotes q ON q.id = (
            SELECT q2.id FROM commodity_quotes q2 WHERE q2.symbol = i.symbol
            ORDER BY CASE WHEN json_valid(q2.raw_json) THEN julianday(COALESCE(
                json_extract(q2.raw_json, '$.quote_at'),
                json_extract(q2.raw_json, '$.updated_at'))) END DESC, q2.id DESC LIMIT 1
        ) WHERE i.active = 1
    """).fetchall()
    result = {}
    for record in rows:
        row = dict(record)
        try:
            raw = json.loads(row.pop("raw_json") or "{}")
            raw = raw if isinstance(raw, dict) else {}
        except (ValueError, TypeError):
            raw = {}
        result[row["symbol"]] = {
            **row,
            **raw,
            "group": "commodities",
            "refresh_failed": True,
            # as_of of legacy rows is a cache write time, never a quote time.
            "updated_at": raw.get("quote_at") or raw.get("updated_at"),
            "fetched_at": raw.get("fetched_at") or row.get("as_of"),
        }
    return result


def _persist_quote(conn, item, instrument):
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO commodity_instruments
          (symbol, name, provider_symbol, category, unit, metadata_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(symbol) DO UPDATE SET name=excluded.name,
          provider_symbol=excluded.provider_symbol, category=excluded.category,
          unit=excluded.unit, metadata_json=excluded.metadata_json, updated_at=excluded.updated_at
    """,
        (
            instrument.symbol,
            instrument.name,
            instrument.yahoo_symbol,
            instrument.category,
            instrument.unit,
            json.dumps({"focus": instrument.focus}),
            now,
            now,
        ),
    )
    if item.get("price") is None or not item.get("updated_at"):
        return
    conn.execute(
        """
        INSERT INTO commodity_quotes
          (symbol, as_of, price, change, change_pct, high_24h, low_24h, volume_24h,
           source, freshness, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(symbol, as_of) DO UPDATE SET
          price=excluded.price, change=excluded.change, change_pct=excluded.change_pct,
          high_24h=excluded.high_24h, low_24h=excluded.low_24h, volume_24h=excluded.volume_24h,
          source=excluded.source, freshness=excluded.freshness, raw_json=excluded.raw_json
    """,
        (
            instrument.symbol,
            item["updated_at"],
            item["price"],
            item.get("change"),
            item.get("change_pct"),
            item.get("high_24h"),
            item.get("low_24h"),
            item.get("volume_24h"),
            item.get("source") or "yahoo_finance",
            item["freshness"],
            json.dumps(item, ensure_ascii=False),
        ),
    )


def sync_commodity_snapshot(*, refresh=False) -> dict[str, Any]:
    producer = GlobalMarketFeedProducer()
    feed = producer.snapshot(read_only=True)
    incoming = {
        row["symbol"]: row
        for row in feed.get("groups", {}).get("commodities", [])
        if row.get("symbol")
    }
    catalog = [
        instrument
        for instrument in market_feed.GLOBAL_MARKET_INSTRUMENTS
        if instrument.group == "commodities"
    ]
    items = []
    with open_db() as conn:
        stored = _stored_quotes(conn)
        for instrument in catalog:
            source = incoming.get(instrument.symbol)
            if not source or finite_number(source.get("price")) is None:
                source = stored.get(instrument.symbol, {})
            row = {
                **source,
                "symbol": instrument.symbol,
                "name": instrument.name,
                "yahoo_symbol": instrument.yahoo_symbol,
                "category": instrument.category,
                "unit": instrument.unit,
                "group": "commodities",
                "focus": instrument.focus,
            }
            row = quote_health(
                row,
                fallback_fetched_at=source.get("fetched_at"),
                max_fetch_age=producer.max_cache_age_seconds,
            )
            items.append(row)
            # Reading a fallback must not rewrite its timestamps or add history.
            if instrument.symbol in incoming:
                _persist_quote(conn, row, instrument)
    summary = quote_summary(items)
    refresh_requested = False
    if refresh or feed.get("freshness") != "fresh":
        refresh_requested = producer.refresh_in_background()
    return {
        **summary,
        "source": "yahoo_finance",
        "provider": "yahoo_finance",
        "data_interval": feed.get("data_interval") or "1d",
        "stale_reason": None
        if summary["freshness"] == "fresh"
        else "some_quotes_unavailable_or_old",
        "refresh_requested": bool(refresh_requested),
        "total": len(items),
        "items": items,
        "storage": "sqlite:commodity_quotes",
    }
