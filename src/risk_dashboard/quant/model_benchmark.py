"""Deprecated shim — use risk_dashboard.engines.quant.model_benchmark."""
from risk_dashboard.engines.quant.model_benchmark import *  # noqa: F403
from risk_dashboard.engines.quant import model_benchmark as _mod
import sys
sys.modules[__name__] = _mod
