"""Deprecated shim — use risk_dashboard.engines.quant.financial_quality_charts."""
from risk_dashboard.engines.quant.financial_quality_charts import *  # noqa: F403
from risk_dashboard.engines.quant import financial_quality_charts as _mod
import sys
sys.modules[__name__] = _mod
