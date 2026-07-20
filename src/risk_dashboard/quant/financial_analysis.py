"""Deprecated shim — use risk_dashboard.engines.quant.financial_analysis."""
from risk_dashboard.engines.quant.financial_analysis import *  # noqa: F403
from risk_dashboard.engines.quant import financial_analysis as _mod
import sys
sys.modules[__name__] = _mod
