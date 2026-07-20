"""Deprecated shim — use risk_dashboard.engines.quant.shap_explain."""
from risk_dashboard.engines.quant.shap_explain import *  # noqa: F403
from risk_dashboard.engines.quant import shap_explain as _mod
import sys
sys.modules[__name__] = _mod
