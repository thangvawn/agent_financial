"""Deprecated shim — use risk_dashboard.engines.quant.eod_pipeline."""
from risk_dashboard.engines.quant.eod_pipeline import *  # noqa: F403
from risk_dashboard.engines.quant import eod_pipeline as _mod
import sys
sys.modules[__name__] = _mod
