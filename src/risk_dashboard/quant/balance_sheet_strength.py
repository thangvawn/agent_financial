"""Deprecated shim — use risk_dashboard.engines.quant.balance_sheet_strength."""
from risk_dashboard.engines.quant.balance_sheet_strength import *  # noqa: F403
from risk_dashboard.engines.quant import balance_sheet_strength as _mod
import sys
sys.modules[__name__] = _mod
