from __future__ import annotations

from dataclasses import dataclass

STARTING_CASH = 100_000_000.0  # educational paper money (VND)


@dataclass
class WatchlistItem:
    item_id: str
    user_id: str
    symbol: str
    label: str
    sort_order: int
    created_at: str


@dataclass
class PaperOrder:
    order_id: str
    user_id: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    limit_price: float | None
    status: str
    filled_qty: float
    filled_price: float | None
    created_at: str
    updated_at: str
    filled_at: str | None


@dataclass
class Holding:
    user_id: str
    symbol: str
    quantity: float
    avg_cost: float
    updated_at: str
