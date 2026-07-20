from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from risk_dashboard.modules.market_portfolio.domain.entities import STARTING_CASH, WatchlistItem
from risk_dashboard.modules.market_portfolio.infrastructure.trading_store import TradingStoreMixin
from risk_dashboard.platform.database import open_app_state_db


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class MarketPortfolioRepository(TradingStoreMixin):
    def list_watchlist(self, user_id: str) -> list[WatchlistItem]:
        with open_app_state_db() as conn:
            rows = conn.execute(
                """
                SELECT item_id, user_id, symbol, label, sort_order, created_at
                FROM mp_watchlist_items WHERE user_id = ?
                ORDER BY sort_order ASC, created_at ASC
                """,
                (user_id,),
            ).fetchall()
        return [WatchlistItem(**dict(row)) for row in rows]

    def add_watchlist(self, user_id: str, symbol: str, label: str = "") -> WatchlistItem:
        symbol = symbol.strip().upper()
        now = _now()
        item = WatchlistItem(
            item_id=str(uuid.uuid4()),
            user_id=user_id,
            symbol=symbol,
            label=label.strip() or symbol,
            sort_order=0,
            created_at=now,
        )
        with open_app_state_db() as conn:
            existing = conn.execute(
                "SELECT item_id FROM mp_watchlist_items WHERE user_id = ? AND symbol = ?",
                (user_id, symbol),
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE mp_watchlist_items SET label = ? WHERE item_id = ?",
                    (item.label, existing["item_id"]),
                )
                conn.commit()
                item.item_id = existing["item_id"]
                return item
            conn.execute(
                """
                INSERT INTO mp_watchlist_items
                (item_id, user_id, symbol, label, sort_order, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (item.item_id, item.user_id, item.symbol, item.label, item.sort_order, item.created_at),
            )
            conn.commit()
        return item

    def remove_watchlist(self, user_id: str, symbol: str) -> bool:
        with open_app_state_db() as conn:
            cur = conn.execute(
                "DELETE FROM mp_watchlist_items WHERE user_id = ? AND symbol = ?",
                (user_id, symbol.strip().upper()),
            )
            conn.commit()
            return cur.rowcount > 0

    def ensure_account(self, user_id: str) -> dict[str, Any]:
        with open_app_state_db() as conn:
            row = conn.execute(
                "SELECT user_id, cash_balance, currency, updated_at FROM mp_paper_accounts WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if row:
                return dict(row)
            now = _now()
            conn.execute(
                "INSERT INTO mp_paper_accounts (user_id, cash_balance, currency, updated_at) VALUES (?, ?, 'VND', ?)",
                (user_id, STARTING_CASH, now),
            )
            conn.commit()
            return {"user_id": user_id, "cash_balance": STARTING_CASH, "currency": "VND", "updated_at": now}

    def set_cash(self, user_id: str, cash: float) -> None:
        with open_app_state_db() as conn:
            conn.execute(
                "UPDATE mp_paper_accounts SET cash_balance = ?, updated_at = ? WHERE user_id = ?",
                (cash, _now(), user_id),
            )
            conn.commit()
