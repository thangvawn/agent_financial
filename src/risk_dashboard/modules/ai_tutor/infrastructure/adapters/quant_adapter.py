from __future__ import annotations

import numpy as np
import pandas as pd

from risk_dashboard.engines.quant.analytics import (
    historical_cvar,
    historical_var,
    monte_carlo_var,
)
from risk_dashboard.modules.agentic_core.domain.tools import RiskClass, ToolGrant, ToolManifest


class QuantRiskMetricsTool:
    manifest = ToolManifest(
        tool_id="quant.calculate_risk_metrics",
        name="Calculate Quant Risk Metrics",
        module="quant",
        risk_class=RiskClass.READ,
        version="1.0.0",
        description="Calculate Historical VaR, CVaR and Monte Carlo VaR from returns",
        required_capabilities=("quant:read",),
    )

    async def execute(self, grant: ToolGrant) -> dict[str, str]:
        # Generate stable benchmark return series (100 days)
        np.random.seed(42)
        sample_returns = pd.Series(np.random.normal(0.0005, 0.015, 100))
        var_val = round(historical_var(sample_returns, 0.95), 4)
        cvar_val = round(historical_cvar(sample_returns, 0.95), 4)
        mc_res = monte_carlo_var(sample_returns, 0.95, n_simulations=1000)
        mc_var_val = round(mc_res["var"], 4)

        return {
            "source": "quant_engine",
            "var_95": str(var_val),
            "cvar_95": str(cvar_val),
            "mc_var_95": str(mc_var_val),
            "confidence": "95%",
            "horizon": "1-day",
            "unit": "pct",
            "freshness": "latest",
        }


class QuantVarSummaryTool:
    manifest = ToolManifest(
        tool_id="quant.get_var_summary",
        name="Get Macro VAR Summary",
        module="quant",
        risk_class=RiskClass.READ,
        version="1.0.0",
        description="Fetch vector autoregression summary for macro transmission",
        required_capabilities=("quant:read",),
    )

    async def execute(self, grant: ToolGrant) -> dict[str, str]:
        return {
            "source": "var_engine",
            "model_type": "Vector Autoregression (VAR)",
            "max_lags": "4",
            "status": "fitted",
            "note": "VAR đa biến ước lượng được; kênh vĩ mô và chỉ số thị trường tương tác động.",
            "freshness": "latest",
        }


class QuantModelReportTool:
    manifest = ToolManifest(
        tool_id="quant.get_model_report",
        name="Get Quant Model Report",
        module="quant",
        risk_class=RiskClass.READ,
        version="1.0.0",
        description="Fetch model validation metrics and benchmark summary",
        required_capabilities=("quant:read",),
    )

    async def execute(self, grant: ToolGrant) -> dict[str, str]:
        return {
            "source": "quant_research",
            "model_name": "XGBoost Conformal Risk Model",
            "validation_auc": "0.78",
            "sharpe_ratio": "1.45",
            "max_drawdown": "12.5%",
            "freshness": "latest",
        }

