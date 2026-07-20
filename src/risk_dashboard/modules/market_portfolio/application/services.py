from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from risk_dashboard.modules.market_portfolio.application.fills import apply_fill, resolve_fill_price
from risk_dashboard.modules.market_portfolio.application.pricing import quote_last_price, quote_map
from risk_dashboard.modules.market_portfolio.domain.entities import PaperOrder, STARTING_CASH
from risk_dashboard.modules.market_portfolio.infrastructure.repository import MarketPortfolioRepository


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _order_dict(order: PaperOrder) -> dict[str, Any]:
    return {
        "order_id": order.order_id,
        "symbol": order.symbol,
        "side": order.side,
        "order_type": order.order_type,
        "quantity": order.quantity,
        "limit_price": order.limit_price,
        "status": order.status,
        "filled_qty": order.filled_qty,
        "filled_price": order.filled_price,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "filled_at": order.filled_at,
    }


class MarketPortfolioService:
    def __init__(self, repo: MarketPortfolioRepository | None = None) -> None:
        self.repo = repo or MarketPortfolioRepository()

    def list_watchlist(self, session_id: str) -> list[dict[str, Any]]:
        items = self.repo.list_watchlist(session_id)
        prices = quote_map([i.symbol for i in items])
        return [
            {
                "item_id": i.item_id,
                "symbol": i.symbol,
                "label": i.label,
                "price": prices.get(i.symbol),
                "created_at": i.created_at,
            }
            for i in items
        ]

    def add_watchlist(self, session_id: str, symbol: str, label: str = "") -> dict[str, Any]:
        item = self.repo.add_watchlist(session_id, symbol, label)
        return {
            "item_id": item.item_id,
            "symbol": item.symbol,
            "label": item.label,
            "price": quote_last_price(item.symbol),
            "created_at": item.created_at,
        }

    def remove_watchlist(self, session_id: str, symbol: str) -> dict[str, bool]:
        return {"removed": self.repo.remove_watchlist(session_id, symbol)}

    def list_orders(self, session_id: str) -> list[dict[str, Any]]:
        return [_order_dict(o) for o in self.repo.list_orders(session_id)]

    def place_order(
        self,
        *,
        session_id: str,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        limit_price: float | None,
    ) -> dict[str, Any]:
        symbol = symbol.strip().upper()
        side = side.upper()
        order_type = order_type.upper()
        if order_type == "LO" and (limit_price is None or limit_price <= 0):
            raise ValueError("LO orders require a positive limit_price.")
        last = quote_last_price(symbol)
        if last is None:
            raise ValueError(f"No market price for {symbol}. Use a VN equity symbol.")
        now = _now()
        order = PaperOrder(
            order_id=str(uuid.uuid4()),
            user_id=session_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=float(quantity),
            limit_price=float(limit_price) if limit_price is not None else None,
            status="OPEN",
            filled_qty=0.0,
            filled_price=None,
            created_at=now,
            updated_at=now,
            filled_at=None,
        )
        fill_price = resolve_fill_price(order, last)
        if fill_price is not None:
            apply_fill(self.repo, order, fill_price)
        else:
            self.repo.save_order(order)
        return _order_dict(order)

    def cancel_order(self, session_id: str, order_id: str) -> dict[str, Any]:
        order = self.repo.get_order(session_id, order_id)
        if order is None:
            raise LookupError("Order not found.")
        if order.status != "OPEN":
            raise ValueError(f"Cannot cancel order in status {order.status}.")
        order.status = "CANCELLED"
        order.updated_at = _now()
        self.repo.save_order(order)
        return _order_dict(order)

    def portfolio_summary(self, session_id: str) -> dict[str, Any]:
        account = self.repo.ensure_account(session_id)
        holdings = self.repo.list_holdings(session_id)
        prices = quote_map([h.symbol for h in holdings])
        positions = []
        market_value = 0.0
        unrealized = 0.0
        for h in holdings:
            mark = prices.get(h.symbol)
            mv = (mark * h.quantity) if mark is not None else None
            cost = h.avg_cost * h.quantity
            upnl = (mv - cost) if mv is not None else None
            if mv is not None:
                market_value += mv
            if upnl is not None:
                unrealized += upnl
            positions.append(
                {
                    "symbol": h.symbol,
                    "quantity": h.quantity,
                    "avg_cost": round(h.avg_cost, 2),
                    "mark_price": mark,
                    "market_value": round(mv, 2) if mv is not None else None,
                    "unrealized_pnl": round(upnl, 2) if upnl is not None else None,
                    "unrealized_pnl_pct": round((upnl / cost) * 100, 2) if upnl is not None and cost else None,
                }
            )
        cash = float(account["cash_balance"])
        equity = cash + market_value
        return {
            "cash_balance": round(cash, 2),
            "currency": account["currency"],
            "starting_cash": STARTING_CASH,
            "market_value": round(market_value, 2),
            "equity": round(equity, 2),
            "unrealized_pnl": round(unrealized, 2),
            "total_pnl": round(equity - STARTING_CASH, 2),
            "total_pnl_pct": round(((equity - STARTING_CASH) / STARTING_CASH) * 100, 2),
            "positions": positions,
            "updated_at": account["updated_at"],
            "disclaimer": "Educational paper trading only — not real brokerage.",
        }

    def reset_portfolio(self, session_id: str) -> dict[str, Any]:
        self.repo.reset_portfolio(session_id)
        return self.portfolio_summary(session_id)
