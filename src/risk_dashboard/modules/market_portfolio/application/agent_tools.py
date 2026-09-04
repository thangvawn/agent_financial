from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import logging
from typing import Any

_LOG = logging.getLogger(__name__)


from risk_dashboard.modules.agentic_core.domain.tools import RiskClass, ToolManifest
from risk_dashboard.modules.data_hub.application.vn_market_feed import VnMarketFeedProducer
from risk_dashboard.modules.market_portfolio.application.exposure import compute_portfolio_exposure
from risk_dashboard.modules.market_portfolio.application.pricing import quote_map
from risk_dashboard.modules.market_portfolio.application.scenarios import run_deterministic_price_shock
from risk_dashboard.modules.market_portfolio.domain.agent_policy import (
    ResourceNotFoundError,
    build_freshness_stamp,
    check_portfolio_ownership,
)
from risk_dashboard.modules.market_portfolio.domain.entities import STARTING_CASH
from risk_dashboard.modules.market_portfolio.domain.ports import ToolContext
from risk_dashboard.modules.market_portfolio.infrastructure.repository import MarketPortfolioRepository
from risk_dashboard.modules.market_portfolio.schemas.agent_tools import (
    ExplainFillInputV1,
    ExplainFillOutputV1,
    FreshnessStampV1,
    GetExposureInputV1,
    GetExposureOutputV1,
    GetMarketSnapshotInputV1,
    GetMarketSnapshotOutputV1,
    GetPortfolioSnapshotInputV1,
    GetPortfolioSnapshotOutputV1,
    MoneyV1,
    PositionV1,
    RunScenarioInputV1,
    RunScenarioOutputV1,
)

MANIFEST_ID = "market_portfolio.tools@1.0.0"

MARKET_GET_SNAPSHOT_MANIFEST = ToolManifest(
    tool_id="market.get_snapshot.v1",
    name="Get Market Snapshot",
    module="market_portfolio",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Fetch current VN market snapshot, index metrics, and symbol quotes with freshness stamp.",
    required_capabilities=("public:market_portfolio:read",),
)

PORTFOLIO_GET_SNAPSHOT_MANIFEST = ToolManifest(
    tool_id="portfolio.get_snapshot.v1",
    name="Get Portfolio Snapshot",
    module="market_portfolio",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Fetch paper portfolio balance, equity, and positions with mark prices.",
    required_capabilities=("account:market_portfolio:read",),
)

PORTFOLIO_GET_EXPOSURE_MANIFEST = ToolManifest(
    tool_id="portfolio.get_exposure.v1",
    name="Get Exposure and Concentration",
    module="market_portfolio",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Compute deterministic portfolio asset allocation, position weights, top3 concentration, and HHI.",
    required_capabilities=("account:market_portfolio:read",),
)

PORTFOLIO_RUN_SCENARIO_MANIFEST = ToolManifest(
    tool_id="portfolio.run_scenario.v1",
    name="Run Price Shock Scenario",
    module="market_portfolio",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Simulate deterministic price shocks on held positions and revalue portfolio equity.",
    required_capabilities=("account:market_portfolio:read",),
)

PORTFOLIO_EXPLAIN_FILL_MANIFEST = ToolManifest(
    tool_id="portfolio.explain_fill.v1",
    name="Explain Paper Order Fill",
    module="market_portfolio",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Provide factual explanation of a completed paper order fill, prices, and timing.",
    required_capabilities=("account:market_portfolio:read",),
)

EXACT_READ_TOOLS: dict[str, ToolManifest] = {
    "market.get_snapshot.v1": MARKET_GET_SNAPSHOT_MANIFEST,
    "portfolio.get_snapshot.v1": PORTFOLIO_GET_SNAPSHOT_MANIFEST,
    "portfolio.get_exposure.v1": PORTFOLIO_GET_EXPOSURE_MANIFEST,
    "portfolio.run_scenario.v1": PORTFOLIO_RUN_SCENARIO_MANIFEST,
    "portfolio.explain_fill.v1": PORTFOLIO_EXPLAIN_FILL_MANIFEST,
}

FORBIDDEN_CATALOG: frozenset[str] = frozenset({
    "portfolio.place_order", "portfolio.submit_order", "portfolio.amend_order",
    "portfolio.cancel_order", "portfolio.reset", "portfolio.reset_cash",
    "portfolio.reset_positions", "watchlist.add", "watchlist.remove",
    "watchlist.reorder", "watchlist.propose_change", "watchlist.confirm_change",
})


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def is_grant_allowed(tool_id: str) -> bool:
    if tool_id in FORBIDDEN_CATALOG:
        return False
    return tool_id in EXACT_READ_TOOLS


async def get_market_snapshot(input: GetMarketSnapshotInputV1, ctx: ToolContext) -> GetMarketSnapshotOutputV1:
    now_iso = ctx.now_iso or _utc_now_iso()
    try:
        feed = VnMarketFeedProducer()
        payload = feed.snapshot()
    except (ConnectionError, TimeoutError, OSError, ValueError, KeyError) as exc:
        _LOG.warning("VnMarketFeedProducer snapshot failed: %s", exc)
        payload = {"items": [], "as_of": now_iso}

    items = payload.get("items", []) or []
    wanted_symbols = {s.upper() for s in input.symbols}
    quotes: list[dict[str, Any]] = []
    found_symbols: set[str] = set()

    for item in items:
        sym = (item.get("symbol") or "").upper()
        if not wanted_symbols or sym in wanted_symbols:
            quotes.append(item)
            found_symbols.add(sym)

    missing = tuple(sorted(wanted_symbols - found_symbols))
    indices_raw = payload.get("indices") or []
    indices = tuple(indices_raw) if isinstance(indices_raw, list) else ()

    if not items and not indices:
        freshness_state: FreshnessState = "unavailable"
        stale_reason = "Market price feed and indices are currently unavailable."
    elif missing or not indices:
        freshness_state = "partial"
        stale_reason = "Partial market feed: some requested symbols or indices are unavailable."
    else:
        freshness_state = "fresh"
        stale_reason = None

    freshness = build_freshness_stamp(
        as_of=payload.get("as_of", now_iso),
        source="vn_market_feed",
        state=freshness_state,
        ttl_seconds=180,
        stale_reason=stale_reason,
    )

    return GetMarketSnapshotOutputV1(
        schema_version="1.0.0",
        market="VN",
        indices=indices,
        breadth=payload.get("breadth"),
        capital_flow=payload.get("capital_flow"),
        quotes=tuple(quotes),
        freshness=freshness,
        missing_symbols=missing,
    )


def _to_decimal(val: float | int | str | Decimal | None) -> Decimal:
    if val is None:
        return Decimal("0.00")
    if isinstance(val, Decimal):
        return val
    return Decimal(str(val))


def _format_money(val: Decimal | float | int | str | None) -> str:
    if val is None:
        return "0.00"
    dec = _to_decimal(val)
    return str(dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


async def get_portfolio_snapshot(input: GetPortfolioSnapshotInputV1, ctx: ToolContext) -> GetPortfolioSnapshotOutputV1:
    account_id = check_portfolio_ownership(ctx.principal, input.portfolio_id)
    now_iso = ctx.now_iso or _utc_now_iso()
    repo = MarketPortfolioRepository()
    account = repo.ensure_account(account_id)
    holdings = repo.list_holdings(account_id)
    quotes = quote_map([h.symbol for h in holdings])

    positions: list[PositionV1] = []
    missing_prices: list[str] = []
    market_value_total = Decimal("0.00")

    for h in holdings:
        mark = quotes.get(h.symbol)
        qty_dec = _to_decimal(h.quantity)
        qty_str = str(h.quantity)
        cost_dec = _to_decimal(h.avg_cost)
        avg_cost_money = MoneyV1(amount=_format_money(cost_dec), currency=account["currency"])

        if mark is None or mark <= 0:
            missing_prices.append(h.symbol)
            positions.append(PositionV1(
                symbol=h.symbol,
                quantity=qty_str,
                avg_cost=avg_cost_money,
                mark_price=None,
                market_value=None,
                unrealized_pnl=None,
                unrealized_pnl_pct=None,
                weight_pct=None,
                freshness=None,
            ))
        else:
            mark_dec = _to_decimal(mark)
            mark_money = MoneyV1(amount=_format_money(mark_dec), currency=account["currency"])
            mv_dec = mark_dec * qty_dec
            cost_total_dec = cost_dec * qty_dec
            upnl_dec = mv_dec - cost_total_dec
            upnl_pct = round(float((upnl_dec / cost_total_dec) * 100), 2) if cost_total_dec > 0 else 0.0
            market_value_total += mv_dec
            positions.append(PositionV1(
                symbol=h.symbol,
                quantity=qty_str,
                avg_cost=avg_cost_money,
                mark_price=mark_money,
                market_value=MoneyV1(amount=_format_money(mv_dec), currency=account["currency"]),
                unrealized_pnl=MoneyV1(amount=_format_money(upnl_dec), currency=account["currency"]),
                unrealized_pnl_pct=upnl_pct,
                weight_pct=None,
                freshness=build_freshness_stamp(as_of=now_iso, source="vn_quote_map", state="fresh"),
            ))

    cash_dec = _to_decimal(account["cash_balance"])
    starting_cash_dec = _to_decimal(STARTING_CASH)
    equity_dec = cash_dec + market_value_total
    total_pnl_dec = equity_dec - starting_cash_dec
    total_pnl_pct = round(float((total_pnl_dec / starting_cash_dec) * 100), 2) if starting_cash_dec > 0 else 0.0

    final_positions: list[PositionV1] = []
    for p in positions:
        w_pct = None
        if p.market_value and equity_dec > 0:
            mv_item = _to_decimal(p.market_value.amount)
            w_pct = round(float((mv_item / equity_dec) * 100), 2)
        final_positions.append(p.model_copy(update={"weight_pct": w_pct}))

    freshness_state: FreshnessState = "partial" if missing_prices else "fresh"
    freshness = build_freshness_stamp(
        as_of=now_iso,
        source="market_portfolio_repository",
        state=freshness_state,
        ttl_seconds=60,
    )
    version_hash = hashlib.sha256(f"{account_id}:{account.get('updated_at')}:{len(holdings)}".encode()).hexdigest()[:16]

    return GetPortfolioSnapshotOutputV1(
        schema_version="1.0.0",
        portfolio_id=input.portfolio_id,
        portfolio_kind="paper",
        snapshot_version=f"snap-{version_hash}",
        cash=MoneyV1(amount=_format_money(cash_dec), currency=account["currency"]),
        starting_cash=MoneyV1(amount=_format_money(starting_cash_dec), currency=account["currency"]),
        market_value=MoneyV1(amount=_format_money(market_value_total), currency=account["currency"]),
        equity=MoneyV1(amount=_format_money(equity_dec), currency=account["currency"]),
        total_pnl=MoneyV1(amount=_format_money(total_pnl_dec), currency=account["currency"]),
        total_pnl_pct=total_pnl_pct,
        positions=tuple(final_positions),
        missing_prices=tuple(missing_prices),
        freshness=freshness,
    )


async def get_exposure(input: GetExposureInputV1, ctx: ToolContext) -> GetExposureOutputV1:

    snap_input = GetPortfolioSnapshotInputV1(portfolio_id=input.portfolio_id)
    snapshot = await get_portfolio_snapshot(snap_input, ctx)
    return compute_portfolio_exposure(
        portfolio_id=snapshot.portfolio_id,
        snapshot_version=snapshot.snapshot_version,
        cash_amount=snapshot.cash.amount,
        positions=snapshot.positions,
        freshness=snapshot.freshness,
    )


async def run_scenario(input: RunScenarioInputV1, ctx: ToolContext) -> RunScenarioOutputV1:
    snap_input = GetPortfolioSnapshotInputV1(portfolio_id=input.portfolio_id)
    snapshot = await get_portfolio_snapshot(snap_input, ctx)
    return run_deterministic_price_shock(
        base_portfolio=snapshot,
        shocks=input.shocks,
        allow_stale=input.allow_stale,
    )


async def explain_fill(input: ExplainFillInputV1, ctx: ToolContext) -> ExplainFillOutputV1:
    account_id = check_portfolio_ownership(ctx.principal, input.portfolio_id)
    now_iso = ctx.now_iso or _utc_now_iso()
    repo = MarketPortfolioRepository()
    order = repo.get_order(account_id, input.order_id)
    if not order:
        raise ResourceNotFoundError("Order not found.")

    facts: list[str] = [
        f"Order ID {order.order_id} for symbol {order.symbol} placed on {order.created_at}.",
        f"Execution type: {order.order_type}, side: {order.side}, requested quantity: {order.quantity}.",
        f"Status: {order.status}, filled quantity: {order.filled_qty}.",
    ]
    if order.filled_price is not None:
        facts.append(f"Filled price: {order.filled_price:,.2f} VND at {order.filled_at or 'n/a'}.")
        if order.limit_price is not None:
            diff = order.filled_price - order.limit_price
            facts.append(f"Limit price was {order.limit_price:,.2f} VND (slippage/delta: {diff:+,.2f} VND).")
    facts.append("Venue: Educational Paper Trading Sandbox (simulated fill, no real brokerage).")

    filled_price_money = MoneyV1(amount=_format_money(order.filled_price), currency="VND") if order.filled_price else None
    limit_price_money = MoneyV1(amount=_format_money(order.limit_price), currency="VND") if order.limit_price else None

    return ExplainFillOutputV1(
        schema_version="1.0.0",
        portfolio_id=input.portfolio_id,
        order_id=input.order_id,
        symbol=order.symbol,
        side="BUY" if order.side == "BUY" else "SELL",
        status=order.status,
        filled_quantity=str(order.filled_qty),
        filled_price=filled_price_money,
        limit_price=limit_price_money,
        created_at=order.created_at,
        filled_at=order.filled_at,
        explanation_facts=tuple(facts),
        freshness=build_freshness_stamp(as_of=now_iso, source="mp_orders", state="fresh"),
    )

