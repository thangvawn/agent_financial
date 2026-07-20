"""Atomic paper-trade fill (single SQLite transaction)."""

from __future__ import annotations

from risk_dashboard.modules.market_portfolio.domain.entities import PaperOrder, STARTING_CASH
from risk_dashboard.platform.database import open_app_state_db


def apply_fill_atomic(order: PaperOrder, fill_price: float, *, now: str) -> None:
    """Account + holdings + cash + order in one BEGIN IMMEDIATE transaction."""
    notional = fill_price * order.quantity
    with open_app_state_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT cash_balance FROM mp_paper_accounts WHERE user_id = ?",
            (order.user_id,),
        ).fetchone()
        if row is None:
            conn.execute(
                """
                INSERT INTO mp_paper_accounts (user_id, cash_balance, currency, updated_at)
                VALUES (?, ?, 'VND', ?)
                """,
                (order.user_id, STARTING_CASH, now),
            )
            cash = float(STARTING_CASH)
        else:
            cash = float(row["cash_balance"])

        holding = conn.execute(
            "SELECT quantity, avg_cost FROM mp_holdings WHERE user_id = ? AND symbol = ?",
            (order.user_id, order.symbol),
        ).fetchone()

        if order.side == "BUY":
            if notional > cash + 1e-6:
                raise ValueError("Insufficient paper cash for this buy.")
            cash -= notional
            if holding is None:
                new_qty, new_avg = order.quantity, fill_price
            else:
                total_cost = float(holding["avg_cost"]) * float(holding["quantity"]) + notional
                new_qty = float(holding["quantity"]) + order.quantity
                new_avg = total_cost / new_qty
            conn.execute(
                """
                INSERT INTO mp_holdings (user_id, symbol, quantity, avg_cost, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, symbol) DO UPDATE SET
                    quantity = excluded.quantity, avg_cost = excluded.avg_cost,
                    updated_at = excluded.updated_at
                """,
                (order.user_id, order.symbol, new_qty, new_avg, now),
            )
        else:
            if holding is None or float(holding["quantity"]) + 1e-9 < order.quantity:
                raise ValueError("Insufficient holdings for this sell.")
            cash += notional
            new_qty = float(holding["quantity"]) - order.quantity
            if new_qty <= 1e-9:
                conn.execute(
                    "DELETE FROM mp_holdings WHERE user_id = ? AND symbol = ?",
                    (order.user_id, order.symbol),
                )
            else:
                conn.execute(
                    """
                    UPDATE mp_holdings SET quantity = ?, updated_at = ?
                    WHERE user_id = ? AND symbol = ?
                    """,
                    (new_qty, now, order.user_id, order.symbol),
                )

        conn.execute(
            "UPDATE mp_paper_accounts SET cash_balance = ?, updated_at = ? WHERE user_id = ?",
            (cash, now, order.user_id),
        )
        order.status = "FILLED"
        order.filled_qty = order.quantity
        order.filled_price = fill_price
        order.filled_at = now
        order.updated_at = now
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
