"""Deprecated shim — use risk_dashboard.engines.quant.advanced_engine."""
from risk_dashboard.engines.quant.advanced_engine import *  # noqa: F403
from risk_dashboard.engines.quant import advanced_engine as _mod
import sys
sys.modules[__name__] = _mod
