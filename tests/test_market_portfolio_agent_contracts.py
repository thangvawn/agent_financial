from __future__ import annotations

import pytest
from pydantic import ValidationError

from risk_dashboard.modules.market_portfolio.application.agent_tools import (
    EXACT_READ_TOOLS,
    FORBIDDEN_CATALOG,
    is_grant_allowed,
)
from risk_dashboard.modules.market_portfolio.schemas import (
    CancelOrderRequest,
    EvidenceRefV1,
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
    PlaceOrderRequest,
    PortfolioReviewArtifactV1,
    PositionV1,
    PriceShockV1,
    ResetPortfolioRequest,
    RunScenarioInputV1,
    RunScenarioOutputV1,
    SCHEMA_VERSION,
    StartPortfolioReviewRequestV1,
    StartPortfolioReviewResponseV1,
    WatchlistAddRequest,
)


def test_schema_version_is_frozen_to_1_0_0():
    assert SCHEMA_VERSION == "1.0.0"


def test_legacy_requests_re_exported_and_functional():
    w = WatchlistAddRequest(session_id="session-12345", symbol="FPT", label="Tech")
    assert w.symbol == "FPT"
    p = PlaceOrderRequest(session_id="session-12345", symbol="FPT", side="BUY", order_type="LO", quantity=100, limit_price=105000.0)
    assert p.quantity == 100
    c = CancelOrderRequest(session_id="session-12345")
    assert c.session_id == "session-12345"
    r = ResetPortfolioRequest(session_id="session-12345")
    assert r.session_id == "session-12345"


def test_strict_model_rejects_extra_fields():
    # Attempting to supply authority fields or unknown fields must fail
    with pytest.raises(ValidationError):
        StartPortfolioReviewRequestV1(
            portfolio_id="port-1",
            review_type="market_context",
            idempotency_key="1234567890123456",
            account_id="spoofed-account",  # extra field
        )

    with pytest.raises(ValidationError):
        StartPortfolioReviewRequestV1(
            portfolio_id="port-1",
            review_type="market_context",
            idempotency_key="1234567890123456",
            session_id="spoofed-session",  # extra field
        )

    with pytest.raises(ValidationError):
        GetPortfolioSnapshotInputV1(
            portfolio_id="port-1",
            account_id="spoofed-account",  # extra field
        )


def test_money_v1_constraints():
    m = MoneyV1(amount="100000.50", currency="VND")
    assert m.currency == "VND"
    assert m.amount == "100000.50"

    with pytest.raises(ValidationError):
        MoneyV1(amount="100", currency="vietnam_dong")  # invalid regex


def test_price_shock_constraints():
    s = PriceShockV1(symbol="FPT", shock_pct=15.0)
    assert s.shock_pct == 15.0

    # Bounds: [-50, 50]
    with pytest.raises(ValidationError):
        PriceShockV1(symbol="FPT", shock_pct=51.0)
    with pytest.raises(ValidationError):
        PriceShockV1(symbol="FPT", shock_pct=-51.0)


def test_idempotency_key_length():
    with pytest.raises(ValidationError):
        StartPortfolioReviewRequestV1(
            portfolio_id="port-1",
            review_type="market_context",
            idempotency_key="short",  # < 16 chars
        )


def test_scenario_request_rejects_duplicates():
    with pytest.raises(ValidationError, match="duplicate symbols"):
        StartPortfolioReviewRequestV1(
            portfolio_id="port-1",
            review_type="scenario",
            idempotency_key="1234567890123456",
            scenario=RunScenarioInputV1(
                portfolio_id="port-1",
                shocks=(
                    PriceShockV1(symbol="FPT", shock_pct=10.0),
                    PriceShockV1(symbol="FPT", shock_pct=-5.0),
                ),
            ),
        )


def test_exact_read_tools_and_forbidden_catalog():
    assert len(EXACT_READ_TOOLS) == 5
    expected_tools = {
        "market.get_snapshot.v1",
        "portfolio.get_snapshot.v1",
        "portfolio.get_exposure.v1",
        "portfolio.run_scenario.v1",
        "portfolio.explain_fill.v1",
    }
    assert set(EXACT_READ_TOOLS.keys()) == expected_tools

    for tool_id in expected_tools:
        assert is_grant_allowed(tool_id) is True

    # Forbidden catalog must refuse grant
    for f in FORBIDDEN_CATALOG:
        assert is_grant_allowed(f) is False

    assert is_grant_allowed("portfolio.place_order") is False
    assert is_grant_allowed("watchlist.add") is False
    assert is_grant_allowed("unknown.tool") is False


def test_tool_context_strict_model():
    from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
    from risk_dashboard.modules.market_portfolio.domain.ports import ToolContext

    principal = AuthPrincipal(account_id="acc-1", session_id="sess-1", resolved_at="2026-09-03T10:00:00Z")
    ctx = ToolContext(principal=principal)
    assert ctx.principal.account_id == "acc-1"

    # StrictModel extra='forbid' must reject extra fields
    with pytest.raises(ValidationError):
        ToolContext(principal=principal, malicious_extra="hacker")


