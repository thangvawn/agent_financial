from __future__ import annotations

import pandas as pd

from risk_dashboard.engines.quant.var_engine import fit_var_summary, var_impulse_note
from risk_dashboard.modules.agentic_core.application.tool_registry import get_default_tool_registry
from risk_dashboard.modules.agentic_core.domain.tools import RiskClass, ToolGrant, ToolManifest


class QuantRiskReadOnlyTool:
    """Read-only domain tool wrapping engines.quant.var_engine."""

    def __init__(self, manifest: ToolManifest | None = None) -> None:
        if manifest is None:
            manifest = get_default_tool_registry().get("quant.explain_risk")
            if manifest is None:
                manifest = ToolManifest(
                    tool_id="quant.explain_risk",
                    name="Explain Quant Risk",
                    module="quant",
                    risk_class=RiskClass.READ,
                    version="1.0.0",
                    description="Explain quantitative risk and VaR metrics.",
                    required_capabilities=("quant:read",),
                )
        self.manifest = manifest

    async def execute(self, grant: ToolGrant) -> dict[str, str]:
        df = pd.DataFrame(
            {
                "vn_index": [1200.0 + (i * 1.5) + (i % 3) for i in range(30)],
                "usd_vnd_rate": [25400.0 + (i * 0.8) - (i % 2) for i in range(30)],
                "sbv_interest_rate_pct": [4.5 + (i * 0.01) for i in range(30)],
            }
        )
        note = var_impulse_note(df, maxlags=1)
        summary = fit_var_summary(df, maxlags=1)
        return {
            "tool_id": self.manifest.tool_id,
            "fitted": str(summary.fitted),
            "n_obs": str(summary.n_obs),
            "note": note,
        }
