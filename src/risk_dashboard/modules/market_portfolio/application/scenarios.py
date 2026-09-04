from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Sequence

from risk_dashboard.modules.market_portfolio.domain.agent_policy import StaleDataBlockedError
from risk_dashboard.modules.market_portfolio.schemas.agent_tools import (
    GetPortfolioSnapshotOutputV1,
    MoneyV1,
    PriceShockV1,
    RunScenarioOutputV1,
)


def _to_decimal(val: str | float | int | None) -> Decimal:
    if val is None:
        return Decimal("0")
    return Decimal(str(val))


def _round_money_str(d: Decimal) -> str:
    return str(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def run_deterministic_price_shock(
    base_portfolio: GetPortfolioSnapshotOutputV1,
    shocks: Sequence[PriceShockV1],
    allow_stale: bool = False,
) -> RunScenarioOutputV1:
    """Apply deterministic mark price shocks to portfolio positions."""
    if base_portfolio.freshness.state == "stale" and not allow_stale:
        raise StaleDataBlockedError("Market data is stale. Scenario blocked unless allow_stale=True.")

    if not shocks:
        raise ValueError("At least one price shock required.")
    if len(shocks) > 30:
        raise ValueError("Maximum 30 price shocks allowed per scenario.")

    shock_symbols = [s.symbol for s in shocks]
    if len(shock_symbols) != len(set(shock_symbols)):
        raise ValueError("Duplicate symbols found in scenario shocks.")

    pos_by_sym = {p.symbol: p for p in base_portfolio.positions}
    for s in shocks:
        if s.symbol not in pos_by_sym:
            raise ValueError(f"Shock symbol '{s.symbol}' is not held in portfolio.")
        if not (-50.0 <= s.shock_pct <= 50.0):
            raise ValueError(f"Shock percentage {s.shock_pct}% must be between -50% and +50%.")

    position_deltas: dict[str, MoneyV1] = {}
    total_delta = Decimal("0")
    currency = base_portfolio.equity.currency

    for s in shocks:
        pos = pos_by_sym[s.symbol]
        if pos.mark_price is None:
            raise ValueError(f"Position '{s.symbol}' has no valid mark price to apply shock.")

        qty_dec = _to_decimal(pos.quantity)
        mark_dec = _to_decimal(pos.mark_price.amount)
        shock_pct_dec = Decimal(str(s.shock_pct))

        old_val = mark_dec * qty_dec
        shock_factor = Decimal("1") + (shock_pct_dec / Decimal("100"))
        new_mark = mark_dec * shock_factor
        new_val = new_mark * qty_dec
        delta = new_val - old_val

        total_delta += delta
        position_deltas[s.symbol] = MoneyV1(
            amount=_round_money_str(delta),
            currency=currency,
        )

    base_eq_dec = _to_decimal(base_portfolio.equity.amount)
    scenario_eq_dec = base_eq_dec + total_delta
    if base_eq_dec > Decimal("0"):
        pnl_delta_pct_dec = (total_delta / base_eq_dec) * Decimal("100")
        pnl_delta_pct = float(pnl_delta_pct_dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    else:
        pnl_delta_pct = 0.0

    limitations = (
        "Linear mark-price shock assuming instant revaluation.",
        "Does not account for liquidity constraints, bid-ask spread, or transaction costs.",
    )

    return RunScenarioOutputV1(
        schema_version="1.0.0",
        portfolio_id=base_portfolio.portfolio_id,
        base_snapshot_version=base_portfolio.snapshot_version,
        assumptions=tuple(shocks),
        base_equity=MoneyV1(amount=_round_money_str(base_eq_dec), currency=currency),
        scenario_equity=MoneyV1(amount=_round_money_str(scenario_eq_dec), currency=currency),
        pnl_delta=MoneyV1(amount=_round_money_str(total_delta), currency=currency),
        pnl_delta_pct=pnl_delta_pct,
        position_deltas=position_deltas,
        deterministic_method="position_mark_price_shock_v1",
        freshness=base_portfolio.freshness,
        limitations=limitations,
    )

