"""Deprecated shim — use risk_dashboard.engines.quant.peer_compare."""
from risk_dashboard.engines.quant.peer_compare import *  # noqa: F403
from risk_dashboard.engines.quant import peer_compare as _mod
import sys
sys.modules[__name__] = _mod
