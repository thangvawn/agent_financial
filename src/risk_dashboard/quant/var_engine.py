"""Deprecated shim — use risk_dashboard.engines.quant.var_engine."""
from risk_dashboard.engines.quant.var_engine import *  # noqa: F403
from risk_dashboard.engines.quant import var_engine as _mod
import sys
sys.modules[__name__] = _mod
