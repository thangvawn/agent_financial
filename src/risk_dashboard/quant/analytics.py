"""Deprecated shim — use risk_dashboard.engines.quant.analytics."""
from risk_dashboard.engines.quant.analytics import *  # noqa: F403
from risk_dashboard.engines.quant import analytics as _mod
import sys
sys.modules[__name__] = _mod
