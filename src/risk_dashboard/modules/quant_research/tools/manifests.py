"""Tool manifests for quant_research capabilities."""
from __future__ import annotations

from risk_dashboard.modules.agentic_core.domain.tools import RiskClass, ToolManifest

QUANT_EOD_MANIFEST = ToolManifest(
    tool_id="quant.eod_analysis.v1",
    name="EOD Quantitative Analysis",
    module="quant_research",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Run canonical end-of-day market risk analysis on panel data.",
    required_capabilities=("quant_research:analysis:read",),
)

QUANT_SCENARIO_MANIFEST = ToolManifest(
    tool_id="quant.scenario_compare.v1",
    name="Macro Scenario Comparison",
    module="quant_research",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Run macro shock scenario comparison with bounded overrides.",
    required_capabilities=("quant_research:scenario:read",),
)

QUANT_MODEL_REPORT_MANIFEST = ToolManifest(
    tool_id="quant.model_report.v1",
    name="Model Research Report",
    module="quant_research",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Fetch latest model evaluation and benchmark metrics.",
    required_capabilities=("quant_research:model_report:read",),
)

ALL_QUANT_TOOL_MANIFESTS: tuple[ToolManifest, ...] = (
    QUANT_EOD_MANIFEST,
    QUANT_SCENARIO_MANIFEST,
    QUANT_MODEL_REPORT_MANIFEST,
)

