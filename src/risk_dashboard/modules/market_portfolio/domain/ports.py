from __future__ import annotations

from typing import Any, Protocol

from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.market_portfolio.schemas.agent_tools import StrictModel


class ToolContext(StrictModel):
    principal: AuthPrincipal
    now_iso: str | None = None
    correlation_id: str | None = None
    run_id: str | None = None



class MarketDataPort(Protocol):
    """Read-only market data access port."""

    def get_market_summary(self) -> Any: ...

    def get_quotes(self, symbols: tuple[str, ...]) -> dict[str, float]: ...

    def get_vn_snapshot_raw(self) -> dict[str, Any]: ...


class PortfolioReaderPort(Protocol):
    """Read-only paper portfolio access port."""

    def get_portfolio_summary(self, account_id: str) -> dict[str, Any]: ...

    def get_order(self, account_id: str, order_id: str) -> Any | None: ...

    def list_holdings(self, account_id: str) -> list[Any]: ...

