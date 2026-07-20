"""Deprecated shim — use risk_dashboard.engines.quant.research_report."""
from risk_dashboard.engines.quant.research_report import *  # noqa: F403
from risk_dashboard.engines.quant import research_report as _mod
import sys
sys.modules[__name__] = _mod
