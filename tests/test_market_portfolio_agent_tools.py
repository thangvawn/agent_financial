from __future__ import annotations

from datetime import datetime, timezone
import pytest


from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.market_portfolio.application.agent_tools import (
    explain_fill,
    get_exposure,
    get_market_snapshot,
    get_portfolio_snapshot,
    run_scenario,
)
from risk_dashboard.modules.market_portfolio.application.exposure import compute_portfolio_exposure
from risk_dashboard.modules.market_portfolio.application.scenarios import run_deterministic_price_shock
from risk_dashboard.modules.market_portfolio.domain.agent_policy import (
    StaleDataBlockedError,
    build_freshness_stamp,
)
from risk_dashboard.modules.market_portfolio.domain.entities import PaperOrder
from risk_dashboard.modules.market_portfolio.domain.ports import ToolContext
from risk_dashboard.modules.market_portfolio.infrastructure.repository import MarketPortfolioRepository
from risk_dashboard.modules.market_portfolio.schemas.agent_tools import (
    ExplainFillInputV1,
    FreshnessStampV1,
    GetExposureInputV1,
    GetMarketSnapshotInputV1,
    GetPortfolioSnapshotInputV1,
    GetPortfolioSnapshotOutputV1,
    MoneyV1,
    PositionV1,
    PriceShockV1,
    RunScenarioInputV1,
)


@pytest.fixture
def sample_freshness() -> FreshnessStampV1:
    return build_freshness_stamp(
        as_of="2026-09-03T10:00:00Z",
        source="unit_test",
        state="fresh",
        ttl_seconds=120,
    )


def test_compute_exposure_golden_metrics(sample_freshness):
    positions = (
        PositionV1(
            symbol="FPT",
            quantity="300",
            avg_cost=MoneyV1(amount="90000.00", currency="VND"),
            mark_price=MoneyV1(amount="100000.00", currency="VND"),
            market_value=MoneyV1(amount="30000000.00", currency="VND"),
        ),
        PositionV1(
            symbol="VNM",
            quantity="250",
            avg_cost=MoneyV1(amount="80000.00", currency="VND"),
            mark_price=MoneyV1(amount="80000.00", currency="VND"),
            market_value=MoneyV1(amount="20000000.00", currency="VND"),
        ),
        PositionV1(
            symbol="HPG",
            quantity="500",
            avg_cost=MoneyV1(amount="20000.00", currency="VND"),
            mark_price=MoneyV1(amount="20000.00", currency="VND"),
            market_value=MoneyV1(amount="10000000.00", currency="VND"),
        ),
    )
    # cash = 40,000,000; total equity = 100,000,000
    res = compute_portfolio_exposure(
        portfolio_id="port-test",
        snapshot_version="v1",
        cash_amount="40000000.00",
        positions=positions,
        freshness=sample_freshness,
    )

    assert res.invested_pct == 60.0
    assert res.cash_pct == 40.0
    assert res.largest_position_pct == 30.0
    assert res.top3_concentration_pct == 60.0
    assert res.weights_pct == {"FPT": 30.0, "VNM": 20.0, "HPG": 10.0}
    # HHI = 0.3^2 + 0.2^2 + 0.1^2 = 0.09 + 0.04 + 0.01 = 0.14
    assert pytest.approx(res.hhi, 0.0001) == 0.14


def test_compute_exposure_missing_mark_excluded(sample_freshness):
    positions = (
        PositionV1(
            symbol="FPT",
            quantity="100",
            avg_cost=MoneyV1(amount="100000.00", currency="VND"),
            mark_price=None,
            market_value=None,
        ),
    )
    res = compute_portfolio_exposure(
        portfolio_id="port-test",
        snapshot_version="v1",
        cash_amount="50000000.00",
        positions=positions,
        freshness=sample_freshness,
    )
    assert res.invested_pct == 0.0
    assert res.cash_pct == 100.0
    assert "FPT" not in res.weights_pct
    assert any("FPT missing mark price" in lim for lim in res.limitations)


def test_compute_exposure_rejects_negative_or_short(sample_freshness):
    short_pos = (
        PositionV1(
            symbol="FPT",
            quantity="-50",
            avg_cost=MoneyV1(amount="100000.00", currency="VND"),
            mark_price=MoneyV1(amount="100000.00", currency="VND"),
            market_value=MoneyV1(amount="-5000000.00", currency="VND"),
        ),
    )
    with pytest.raises(ValueError, match="Short positions not supported"):
        compute_portfolio_exposure("p1", "v1", "10000000.00", short_pos, sample_freshness)


def test_deterministic_scenario_price_shock(sample_freshness):
    pos = (
        PositionV1(
            symbol="FPT",
            quantity="100",
            avg_cost=MoneyV1(amount="100000.00", currency="VND"),
            mark_price=MoneyV1(amount="100000.00", currency="VND"),
            market_value=MoneyV1(amount="10000000.00", currency="VND"),
        ),
    )
    base = GetPortfolioSnapshotOutputV1(
        schema_version="1.0.0",
        portfolio_id="p1",
        snapshot_version="s1",
        cash=MoneyV1(amount="10000000.00", currency="VND"),
        starting_cash=MoneyV1(amount="20000000.00", currency="VND"),
        market_value=MoneyV1(amount="10000000.00", currency="VND"),
        equity=MoneyV1(amount="20000000.00", currency="VND"),
        total_pnl=MoneyV1(amount="0.00", currency="VND"),
        total_pnl_pct=0.0,
        positions=pos,
        freshness=sample_freshness,
    )

    shocks = (PriceShockV1(symbol="FPT", shock_pct=10.0),)
    out = run_deterministic_price_shock(base, shocks)

    assert out.deterministic_method == "position_mark_price_shock_v1"
    assert out.base_equity.amount == "20000000.00"
    # Delta = 100 * 100,000 * 10% = 1,000,000
    assert out.pnl_delta.amount == "1000000.00"
    assert out.scenario_equity.amount == "21000000.00"
    assert out.pnl_delta_pct == 5.0  # 1M / 20M = 5%
    assert out.position_deltas["FPT"].amount == "1000000.00"


def test_build_freshness_stamp_dynamic_behavior():
    from datetime import datetime, timezone
    from risk_dashboard.modules.market_portfolio.domain.agent_policy import build_freshness_stamp

    # 1. As-of in past exceeding TTL produces stale state dynamically
    old_time = "2020-01-01T00:00:00Z"
    stamp_stale = build_freshness_stamp(as_of=old_time, source="vn_feed", ttl_seconds=60)
    assert stamp_stale.state == "stale"
    assert stamp_stale.age_seconds > 1000
    assert stamp_stale.confidence_label == "low"
    assert "exceeds TTL" in (stamp_stale.stale_reason or "")

    # 2. As-of now within TTL produces fresh state
    now_iso = datetime.now(timezone.utc).isoformat()
    stamp_fresh = build_freshness_stamp(as_of=now_iso, source="vn_feed", ttl_seconds=60)
    assert stamp_fresh.state == "fresh"
    assert stamp_fresh.age_seconds <= 5

    # 3. HOSE Market session check: Sunday is closed
    sunday_dt = datetime(2026, 9, 6, 3, 0, 0, tzinfo=timezone.utc)  # Sunday 10:00 ICT
    stamp_weekend = build_freshness_stamp(as_of=now_iso, source="vn_feed", now_dt=sunday_dt)
    assert stamp_weekend.market_session == "closed"


def test_scenario_stale_data_policy():
    from risk_dashboard.modules.market_portfolio.domain.agent_policy import build_freshness_stamp

    # Generate genuine stale freshness via build_freshness_stamp (as_of 1 hour ago with TTL 60s)
    stale_as_of = "2026-09-03T09:00:00Z"
    now_test = datetime(2026, 9, 3, 10, 0, 0, tzinfo=timezone.utc)
    stale_freshness = build_freshness_stamp(
        as_of=stale_as_of,
        source="repo",
        ttl_seconds=60,
        now_dt=now_test,
    )
    assert stale_freshness.state == "stale"

    base = GetPortfolioSnapshotOutputV1(
        schema_version="1.0.0",
        portfolio_id="p1",
        snapshot_version="s1",
        cash=MoneyV1(amount="10000000.00", currency="VND"),
        starting_cash=MoneyV1(amount="10000000.00", currency="VND"),
        market_value=MoneyV1(amount="0.00", currency="VND"),
        equity=MoneyV1(amount="10000000.00", currency="VND"),
        total_pnl=MoneyV1(amount="0.00", currency="VND"),
        total_pnl_pct=0.0,
        positions=(),
        freshness=stale_freshness,
    )
    # Blocked when allow_stale=False
    with pytest.raises(StaleDataBlockedError):
        run_deterministic_price_shock(base, (), allow_stale=False)

    # Allowed when allow_stale=True (with empty shocks it raises ValueError about empty shocks)
    with pytest.raises(ValueError, match="At least one price shock required"):
        run_deterministic_price_shock(base, (), allow_stale=True)



def test_agent_tools_execution_live_reads(monkeypatch):
    import asyncio
    from risk_dashboard.modules.market_portfolio.application import agent_tools as at_mod
    monkeypatch.setattr(at_mod, "quote_map", lambda symbols: {s: 100000.0 for s in symbols})

    async def _run():
        account_id = "test-agent-account-tools"
        principal = AuthPrincipal(account_id=account_id, session_id="sess-tool-test", resolved_at="2026-09-03T10:00:00Z")
        ctx = ToolContext(principal=principal)


        # 1. market.get_snapshot.v1
        m_out = await get_market_snapshot(GetMarketSnapshotInputV1(), ctx)
        assert m_out.schema_version == "1.0.0"
        assert m_out.market == "VN"
        assert m_out.freshness.source == "vn_market_feed"

        # 2. portfolio.get_snapshot.v1
        p_out = await get_portfolio_snapshot(GetPortfolioSnapshotInputV1(portfolio_id=account_id), ctx)
        assert p_out.portfolio_id == account_id
        assert p_out.portfolio_kind == "paper"
        assert float(p_out.cash.amount) >= 0

        # 3. portfolio.get_exposure.v1
        e_out = await get_exposure(GetExposureInputV1(portfolio_id=account_id), ctx)
        assert e_out.portfolio_id == account_id
        assert e_out.invested_pct >= 0

        # 4. portfolio.explain_fill.v1
        repo = MarketPortfolioRepository()
        order = PaperOrder(
            order_id="ord-test-fill",
            user_id=account_id,
            symbol="FPT",
            side="BUY",
            order_type="LO",
            quantity=100.0,
            limit_price=105000.0,
            status="FILLED",
            filled_qty=100.0,
            filled_price=104500.0,
            created_at="2026-09-03T09:30:00Z",
            updated_at="2026-09-03T09:31:00Z",
            filled_at="2026-09-03T09:31:00Z",
        )
        repo.save_order(order)

        fill_out = await explain_fill(ExplainFillInputV1(portfolio_id=account_id, order_id="ord-test-fill"), ctx)
        assert fill_out.symbol == "FPT"
        assert fill_out.side == "BUY"
        assert fill_out.filled_price is not None
        assert fill_out.filled_price.amount == "104500.00"
        assert any("Limit price was 105,000.00 VND" in fact for fact in fill_out.explanation_facts)

    asyncio.run(_run())

