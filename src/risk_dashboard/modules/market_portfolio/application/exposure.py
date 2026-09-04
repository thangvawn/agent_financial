from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Sequence

from risk_dashboard.modules.market_portfolio.schemas.agent_tools import (
    FreshnessStampV1,
    GetExposureOutputV1,
    PositionV1,
)


def _to_decimal(val: str | float | int | None) -> Decimal:
    if val is None:
        return Decimal("0")
    return Decimal(str(val))


def _round_float(d: Decimal, places: int = 4) -> float:
    return float(d.quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP))


def compute_portfolio_exposure(
    portfolio_id: str,
    snapshot_version: str,
    cash_amount: str,
    positions: Sequence[PositionV1],
    freshness: FreshnessStampV1,
) -> GetExposureOutputV1:
    """Compute portfolio weights, cash ratio, concentration metrics, and HHI deterministically."""
    cash_dec = _to_decimal(cash_amount)
    if cash_dec < Decimal("0"):
        raise ValueError("Cash cannot be negative.")

    limitations: list[str] = []
    market_value_total = Decimal("0")
    position_mvs: dict[str, Decimal] = {}

    for pos in positions:
        qty_dec = _to_decimal(pos.quantity)
        if qty_dec < Decimal("0"):
            raise ValueError(f"Short positions not supported in Phase 1: {pos.symbol} quantity {pos.quantity}")

        if pos.mark_price is None or pos.market_value is None:
            limitations.append(f"Position {pos.symbol} missing mark price; excluded from exposure weights.")
            continue

        mv_dec = _to_decimal(pos.market_value.amount)
        if mv_dec < Decimal("0"):
            raise ValueError(f"Position {pos.symbol} has negative market value.")

        position_mvs[pos.symbol] = mv_dec
        market_value_total += mv_dec

    equity_dec = cash_dec + market_value_total

    if equity_dec <= Decimal("0"):
        return GetExposureOutputV1(
            schema_version="1.0.0",
            portfolio_id=portfolio_id,
            snapshot_version=snapshot_version,
            invested_pct=0.0,
            cash_pct=0.0,
            largest_position_pct=None,
            top3_concentration_pct=None,
            hhi=None,
            weights_pct={},
            limitations=tuple(limitations + ["Total equity is zero or negative; concentration metrics undefined."]),
            freshness=freshness,
        )

    invested_pct_dec = (market_value_total / equity_dec) * Decimal("100")
    cash_pct_dec = (cash_dec / equity_dec) * Decimal("100")

    weights_pct: dict[str, float] = {}
    weight_fractions: list[Decimal] = []

    for sym, mv in position_mvs.items():
        w_dec = (mv / equity_dec) * Decimal("100")
        weights_pct[sym] = _round_float(w_dec, 2)
        weight_fractions.append(mv / equity_dec)

    sorted_mvs = sorted(position_mvs.values(), reverse=True)
    largest_position_pct: float | None = None
    if sorted_mvs:
        largest_dec = (sorted_mvs[0] / equity_dec) * Decimal("100")
        largest_position_pct = _round_float(largest_dec, 2)

    top3_concentration_pct: float | None = None
    if sorted_mvs:
        top3_dec = (sum(sorted_mvs[:3]) / equity_dec) * Decimal("100")
        top3_concentration_pct = _round_float(top3_dec, 2)

    # HHI (Herfindahl-Hirschman Index) on [0, 1] scale across invested positions
    # If no invested positions, HHI is 0.0
    hhi: float | None = None
    if weight_fractions:
        hhi_dec = sum(w ** 2 for w in weight_fractions)
        hhi = _round_float(hhi_dec, 4)
    else:
        hhi = 0.0

    return GetExposureOutputV1(
        schema_version="1.0.0",
        portfolio_id=portfolio_id,
        snapshot_version=snapshot_version,
        invested_pct=_round_float(invested_pct_dec, 2),
        cash_pct=_round_float(cash_pct_dec, 2),
        largest_position_pct=largest_position_pct,
        top3_concentration_pct=top3_concentration_pct,
        hhi=hhi,
        weights_pct=weights_pct,
        limitations=tuple(limitations),
        freshness=freshness,
    )

