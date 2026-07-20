"""Deprecated shim — use risk_dashboard.engines.quant.backtest."""
from risk_dashboard.engines.quant.backtest import *  # noqa: F403
from risk_dashboard.engines.quant import backtest as _mod
import sys
sys.modules[__name__] = _mod
