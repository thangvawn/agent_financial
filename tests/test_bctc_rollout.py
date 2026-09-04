from __future__ import annotations

import pytest

from risk_dashboard.app.registry.registry import get_module_by_slug
from risk_dashboard.modules.financials_product.agent_tools import get_bctc_tool_manifests
from risk_dashboard.modules.financials_product.api.public import (
    _income_formulas,
    _line_item_explanations,
    _load_dataset_or_503,
)
from risk_dashboard.modules.financials_product.application import build_company_financial_workspace


def test_bctc_agent_subflag_registered():
    mod = get_module_by_slug("financials_product")
    assert mod is not None
    assert "module.financials_product.enabled" in mod.feature_flags
    assert "module.financials_product.bctc_agent.enabled" in mod.feature_flags


def test_deterministic_bctc_unaffected_by_agent_flag():
    """Verify standard deterministic BCTC functionality works standalone."""
    formulas = _income_formulas()
    assert len(formulas) >= 7

    explanations = _line_item_explanations()
    assert "revenue" in explanations
    assert "gross_profit" in explanations

    # Dataset loading
    dataset = _load_dataset_or_503("FPT")
    assert dataset.ticker == "FPT"
    assert len(dataset.periods) > 0

    # Workspace generation
    workspace = build_company_financial_workspace(dataset)
    assert workspace is not None


def test_tool_manifests_cost_and_sla_metadata():
    manifests = get_bctc_tool_manifests()
    assert len(manifests) == 6
    for m in manifests:
        assert m.risk_class.value == "read"
        assert m.module == "financials_product"
        assert m.version == "1.0.0"
