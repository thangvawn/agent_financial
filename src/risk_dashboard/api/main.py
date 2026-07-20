from __future__ import annotations

from risk_dashboard.app.bootstrap.app_factory import create_app
from risk_dashboard.data import cross_asset_prices as cross_asset_prices_mod
from risk_dashboard.data import watchlist_prices as watchlist_prices_mod
from risk_dashboard.platform.runtime.panel_store import (
    autoload_default_panel,
    get_panel,
    panel_date_range,
    panel_status,
    set_panel_for_testing,
    set_panel_from_frame,
)
from risk_dashboard.engines.quant.backtest import run_vn_portfolio_backtest

app = create_app()

__all__ = [
    "app",
    "autoload_default_panel",
    "cross_asset_prices_mod",
    "get_panel",
    "panel_date_range",
    "panel_status",
    "run_vn_portfolio_backtest",
    "set_panel_for_testing",
    "set_panel_from_frame",
    "watchlist_prices_mod",
]
