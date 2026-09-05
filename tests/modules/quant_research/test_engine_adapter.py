"""Tests for QuantEngineAdapter (QF1 Exit Gate & Parity Backtest)."""
from __future__ import annotations

from datetime import date
from unittest.mock import patch
import pytest

from risk_dashboard.engines.quant.eod_pipeline import run_quant_eod
from risk_dashboard.engines.quant.research_report import build_model_research_report
from risk_dashboard.engines.quant.scenario import rerun_with_macro_override
from risk_dashboard.modules.quant_research.infrastructure.engine_adapter import (
    QuantAdapterError,
    QuantEngineAdapter,
)
from risk_dashboard.platform.runtime.panel_store import (
    PanelUnavailableError,
    set_panel_for_testing,
)


@pytest.fixture(autouse=True)
def setup_panel(synthetic_panel):
    set_panel_for_testing(synthetic_panel)
    return synthetic_panel


@pytest.mark.anyio
async def test_eod_analysis_parity_with_direct_engine(synthetic_panel, as_of_date) -> None:
    """Parity backtest: adapter output exact-equals direct run_quant_eod."""
    adapter = QuantEngineAdapter()

    # 1. Direct canonical call
    direct = run_quant_eod(synthetic_panel, as_of_date, run_id="test-eod-direct")

    # 2. Adapter call
    tool_result = await adapter.run_eod_analysis(as_of=as_of_date, run_id="test-eod-direct")

    assert tool_result.status == "ok"
    assert tool_result.tool_name == "quant.eod_analysis.v1"
    assert len(tool_result.source_refs) == 3

    payload = tool_result.payload
    assert payload["run_id"] == "test-eod-direct"
    assert payload["decision_score"] == direct.decision_score
    assert payload["risk_regime"] == direct.risk_regime
    assert payload["horizons"]["p_decline_1w"] == direct.horizons.p_decline_1w
    assert payload["horizons"]["p_decline_2w"] == direct.horizons.p_decline_2w
    assert payload["horizons"]["p_decline_1m"] == direct.horizons.p_decline_1m
    assert payload["dominant_feature"] == direct.dominant_feature
    assert payload["provenance"] == direct.provenance.model_dump(mode="json")
    assert payload["shap_top"] == [item.model_dump(mode="json") for item in direct.shap_top]


@pytest.mark.anyio
async def test_scenario_compare_parity_with_direct_engine(synthetic_panel, as_of_date) -> None:
    """Parity backtest: adapter output exact-equals direct rerun_with_macro_override."""
    adapter = QuantEngineAdapter()

    # 1. Direct canonical call
    direct = rerun_with_macro_override(
        synthetic_panel,
        as_of_date,
        usd_vnd_rate=26000.0,
        sbv_interest_rate_pct=5.5,
    )

    # 2. Adapter call
    tool_result = await adapter.compare_macro_scenario(
        as_of=as_of_date,
        usd_vnd_rate=26000.0,
        sbv_interest_rate_pct=5.5,
    )

    assert tool_result.status == "ok"
    assert tool_result.tool_name == "quant.scenario_compare.v1"
    assert len(tool_result.source_refs) == 3

    payload = tool_result.payload
    assert payload["decision_score"] == direct.decision_score
    assert payload["risk_regime"] == direct.risk_regime
    assert payload["horizons"]["p_decline_1w"] == direct.horizons.p_decline_1w
    assert payload["horizons"]["p_decline_2w"] == direct.horizons.p_decline_2w
    assert payload["horizons"]["p_decline_1m"] == direct.horizons.p_decline_1m


@pytest.mark.anyio
async def test_model_research_report_latest() -> None:
    adapter = QuantEngineAdapter()
    tool_result = await adapter.get_model_research_report(model_ref="latest")

    assert tool_result.status == "ok"
    assert tool_result.tool_name == "quant.model_report.v1"
    direct_report = build_model_research_report("data/models")
    assert tool_result.payload["summary"]["model_version"] == direct_report.summary["model_version"]
    assert tool_result.payload["evidence_status"] == "available"


@pytest.mark.anyio
async def test_model_research_report_rejects_path_injection() -> None:
    adapter = QuantEngineAdapter()
    with pytest.raises(QuantAdapterError) as exc_info:
        await adapter.get_model_research_report(model_ref="/etc/passwd")  # type: ignore[arg-type]
    assert exc_info.value.error_type == "invalid_input"
    assert "arbitrary paths are forbidden" in exc_info.value.message


@pytest.mark.anyio
async def test_date_out_of_range_raises_typed_error() -> None:
    adapter = QuantEngineAdapter()
    invalid_date = date(1985, 1, 1)

    with pytest.raises(QuantAdapterError) as exc_info:
        await adapter.run_eod_analysis(as_of=invalid_date)
    assert exc_info.value.error_type == "date_out_of_range"
    assert "not present in available panel" in exc_info.value.message


@pytest.mark.anyio
async def test_panel_unavailable_raises_typed_error() -> None:
    adapter = QuantEngineAdapter()
    with patch(
        "risk_dashboard.modules.quant_research.infrastructure.engine_adapter.get_panel",
        side_effect=PanelUnavailableError({"message": "Database connection dropped"}),
    ):
        with pytest.raises(QuantAdapterError) as exc_info:
            await adapter.run_eod_analysis(as_of=date(2026, 3, 30))
        assert exc_info.value.error_type == "panel_unavailable"


@pytest.mark.anyio
async def test_model_unavailable_raises_typed_error() -> None:
    adapter = QuantEngineAdapter(models_dir="/tmp/nonexistent_models_dir_abc123")
    with pytest.raises(QuantAdapterError) as exc_info:
        await adapter.get_model_research_report(model_ref="latest")
    assert exc_info.value.error_type == "model_unavailable"
