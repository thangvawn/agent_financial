"""Commodity market repository and provider sync for the market-portfolio desk."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any

from risk_dashboard.modules.data_hub.application.global_market_feed import GlobalMarketFeedProducer
from risk_dashboard.platform.database.connection import open_db


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sync_commodity_snapshot() -> dict[str, Any]:
    feed = GlobalMarketFeedProducer().snapshot()
    items = list(feed.get("groups", {}).get("commodities", []))
    as_of = feed.get("as_of") or _now()
    freshness = feed.get("freshness") or "degraded"
    with open_db() as conn:
        for item in items:
            symbol = str(item.get("symbol", "")).upper()
            if not symbol:
                continue
            conn.execute(
                """
                INSERT INTO commodity_instruments
                  (symbol, name, provider_symbol, category, unit, metadata_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                  name=excluded.name, provider_symbol=excluded.provider_symbol,
                  category=excluded.category, unit=excluded.unit,
                  metadata_json=excluded.metadata_json, updated_at=excluded.updated_at
                """,
                (
                    symbol,
                    item.get("name") or symbol,
                    item.get("yahoo_symbol"),
                    item.get("category") or "other",
                    item.get("unit") or "—",
                    json.dumps({"focus": item.get("focus")}, ensure_ascii=False),
                    _now(),
                    _now(),
                ),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO commodity_quotes
                  (symbol, as_of, price, change, change_pct, high_24h, low_24h,
                   volume_24h, source, freshness, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    symbol,
                    as_of,
                    item.get("price"),
                    item.get("change"),
                    item.get("change_pct"),
                    item.get("high_24h"),
                    item.get("low_24h"),
                    item.get("volume_24h"),
                    item.get("source") or feed.get("source") or "unknown",
                    freshness,
                    json.dumps(item, ensure_ascii=False, default=str),
                ),
            )

        if not items:
            rows = conn.execute(
                """
                SELECT i.symbol, i.name, i.provider_symbol AS yahoo_symbol,
                       i.category, i.unit, q.as_of, q.price, q.change,
                       q.change_pct, q.high_24h, q.low_24h, q.volume_24h,
                       q.source, q.freshness
                FROM commodity_instruments i
                JOIN commodity_quotes q ON q.id = (
                  SELECT q2.id FROM commodity_quotes q2
                  WHERE q2.symbol = i.symbol ORDER BY q2.as_of DESC LIMIT 1
                )
                WHERE i.active = 1 ORDER BY i.category, i.symbol
                """
            ).fetchall()
            items = [dict(row) for row in rows]

    return {
        "as_of": as_of,
        "source": feed.get("source", "yahoo_finance"),
        "provider": "yahoo_finance",
        "data_interval": "1d",
        "freshness": freshness,
        "stale_reason": feed.get("stale_reason"),
        "total": len(items),
        "items": items,
        "storage": "sqlite:commodity_quotes",
    }
