from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from risk_dashboard.modules.market_portfolio.domain.entities import Holding, PaperOrder, STARTING_CASH
from risk_dashboard.platform.database import open_app_state_db


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _order_from_row(row: Any) -> PaperOrder:
    return PaperOrder(
        order_id=row["order_id"],
        user_id=row["user_id"],
        symbol=row["symbol"],
        side=row["side"],
        order_type=row["order_type"],
        quantity=float(row["quantity"]),
        limit_price=float(row["limit_price"]) if row["limit_price"] is not None else None,
        status=row["status"],
        filled_qty=float(row["filled_qty"] or 0),
        filled_price=float(row["filled_price"]) if row["filled_price"] is not None else None,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        filled_at=row["filled_at"],
    )


class TradingStoreMixin:
    def list_orders(self, user_id: str, limit: int = 50) -> list[PaperOrder]:
        with open_app_state_db() as conn:
            rows = conn.execute(
                """
                SELECT order_id, user_id, symbol, side, order_type, quantity, limit_price,
                       status, filled_qty, filled_price, created_at, updated_at, filled_at
                FROM mp_orders WHERE user_id = ?
                ORDER BY created_at DESC LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        return [_order_from_row(row) for row in rows]

    def get_order(self, user_id: str, order_id: str) -> PaperOrder | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT order_id, user_id, symbol, side, order_type, quantity, limit_price,
                       status, filled_qty, filled_price, created_at, updated_at, filled_at
                FROM mp_orders WHERE user_id = ? AND order_id = ?
                """,
                (user_id, order_id),
            ).fetchone()
        return _order_from_row(row) if row else None

    def save_order(self, order: PaperOrder) -> PaperOrder:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO mp_orders (
                    order_id, user_id, symbol, side, order_type, quantity, limit_price,
                    status, filled_qty, filled_price, created_at, updated_at, filled_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(order_id) DO UPDATE SET
                    status = excluded.status, filled_qty = excluded.filled_qty,
                    filled_price = excluded.filled_price, updated_at = excluded.updated_at,
                    filled_at = excluded.filled_at
                """,
                (
                    order.order_id, order.user_id, order.symbol, order.side, order.order_type,
                    order.quantity, order.limit_price, order.status, order.filled_qty,
                    order.filled_price, order.created_at, order.updated_at, order.filled_at,
                ),
            )
            conn.commit()
        return order

    def list_holdings(self, user_id: str) -> list[Holding]:
        with open_app_state_db() as conn:
            rows = conn.execute(
                """
                SELECT user_id, symbol, quantity, avg_cost, updated_at FROM mp_holdings
                WHERE user_id = ? AND quantity > 0 ORDER BY symbol ASC
                """,
                (user_id,),
            ).fetchall()
        return [Holding(**dict(row)) for row in rows]

    def get_holding(self, user_id: str, symbol: str) -> Holding | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT user_id, symbol, quantity, avg_cost, updated_at FROM mp_holdings
                WHERE user_id = ? AND symbol = ?
                """,
                (user_id, symbol),
            ).fetchone()
        return Holding(**dict(row)) if row else None

    def upsert_holding(self, holding: Holding) -> None:
        with open_app_state_db() as conn:
            if holding.quantity <= 1e-9:
                conn.execute(
                    "DELETE FROM mp_holdings WHERE user_id = ? AND symbol = ?",
                    (holding.user_id, holding.symbol),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO mp_holdings (user_id, symbol, quantity, avg_cost, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, symbol) DO UPDATE SET
                        quantity = excluded.quantity, avg_cost = excluded.avg_cost,
                        updated_at = excluded.updated_at
                    """,
                    (holding.user_id, holding.symbol, holding.quantity, holding.avg_cost, holding.updated_at),
                )
            conn.commit()

    def reset_portfolio(self, user_id: str) -> dict[str, Any]:
        now = _now()
        with open_app_state_db() as conn:
            conn.execute("DELETE FROM mp_orders WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM mp_holdings WHERE user_id = ?", (user_id,))
            conn.execute(
                """
                INSERT INTO mp_paper_accounts (user_id, cash_balance, currency, updated_at)
                VALUES (?, ?, 'VND', ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    cash_balance = excluded.cash_balance, updated_at = excluded.updated_at
                """,
                (user_id, STARTING_CASH, now),
            )
        return self.ensure_account(user_id)  # type: ignore[attr-defined]
