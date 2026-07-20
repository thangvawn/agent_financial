"""Deprecated shim — use risk_dashboard.engines.quant.scenario."""
from risk_dashboard.engines.quant.scenario import *  # noqa: F403
from risk_dashboard.engines.quant import scenario as _mod
import sys
sys.modules[__name__] = _mod
