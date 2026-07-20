from __future__ import annotations

from datetime import datetime, timezone

from risk_dashboard.modules.market_portfolio.application.fill_tx import apply_fill_atomic
from risk_dashboard.modules.market_portfolio.domain.entities import PaperOrder


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def resolve_fill_price(order: PaperOrder, last: float) -> float | None:
    if order.order_type == "MP":
        return last
    if order.limit_price is None:
        raise ValueError("limit_price required for non-MP orders.")
    if order.side == "BUY" and last <= order.limit_price:
        return last
    if order.side == "SELL" and last >= order.limit_price:
        return last
    return None


def apply_fill(_repo, order: PaperOrder, fill_price: float) -> None:
    """Fill order + update cash/holdings in one SQLite transaction."""
    apply_fill_atomic(order, fill_price, now=_now())
