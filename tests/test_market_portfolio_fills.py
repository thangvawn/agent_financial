from __future__ import annotations

import pytest

from risk_dashboard.modules.market_portfolio.application.fills import apply_fill, resolve_fill_price
from risk_dashboard.modules.market_portfolio.domain.entities import PaperOrder, STARTING_CASH
from risk_dashboard.modules.market_portfolio.infrastructure.repository import MarketPortfolioRepository
from risk_dashboard.platform.database import open_app_state_db, reset_app_state_tables


def _order(**kwargs) -> PaperOrder:
    base = dict(
        order_id="ord-1",
        user_id="user-fill-test",
        symbol="FPT",
        side="BUY",
        order_type="MP",
        quantity=10.0,
        limit_price=None,
        status="OPEN",
        filled_qty=0.0,
        filled_price=None,
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
        filled_at=None,
    )
    base.update(kwargs)
    return PaperOrder(**base)


def test_resolve_fill_price_requires_limit_for_lo():
    order = _order(order_type="LO", limit_price=None)
    with pytest.raises(ValueError, match="limit_price"):
        resolve_fill_price(order, 100.0)


def test_apply_fill_buy_and_reject_overspend():
    reset_app_state_tables()
    repo = MarketPortfolioRepository()
    user = "user-fill-test"
    repo.ensure_account(user)

    buy = _order(order_id="b1", quantity=10.0)
    apply_fill(repo, buy, 100_000.0)
    assert buy.status == "FILLED"

    with open_app_state_db() as conn:
        cash = float(
            conn.execute(
                "SELECT cash_balance FROM mp_paper_accounts WHERE user_id = ?", (user,)
            ).fetchone()["cash_balance"]
        )
        qty = float(
            conn.execute(
                "SELECT quantity FROM mp_holdings WHERE user_id = ? AND symbol = ?",
                (user, "FPT"),
            ).fetchone()["quantity"]
        )
    assert cash == STARTING_CASH - 1_000_000.0
    assert qty == 10.0

    huge = _order(order_id="b2", quantity=10_000_000.0)
    with pytest.raises(ValueError, match="Insufficient paper cash"):
        apply_fill(repo, huge, 100_000.0)


def test_apply_fill_sell_rejects_without_holdings():
    reset_app_state_tables()
    repo = MarketPortfolioRepository()
    sell = _order(order_id="s1", side="SELL", quantity=1.0)
    with pytest.raises(ValueError, match="Insufficient holdings"):
        apply_fill(repo, sell, 100_000.0)
