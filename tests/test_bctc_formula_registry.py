from __future__ import annotations

import pytest

from risk_dashboard.modules.financials_product.api.public import _income_formulas
from risk_dashboard.modules.financials_product.domain.formula_registry import (
    FormulaEntry,
    _FORMULA_REGISTRY,
    get_formula,
    list_all_formulas,
    list_approved_formulas,
)


def test_registry_has_7_formulas():
    formulas = list_all_formulas()
    assert len(formulas) == 7
    ids = {f.formula_id for f in formulas}
    expected = {
        "gross_profit",
        "gross_margin",
        "operating_margin",
        "net_margin",
        "yoy_growth",
        "qoq_growth",
        "cost_to_revenue_ratio",
    }
    assert ids == expected


def test_get_approved_formula():
    entry = get_formula("gross_margin")
    assert isinstance(entry, FormulaEntry)
    assert entry.formula_id == "gross_margin"
    assert entry.version == "1.0.0"
    assert entry.unit == "pct"
    assert entry.approved is True
    assert entry.approved_by == "domain_expert"
    assert entry.approved_at is not None


def test_get_unapproved_raises(monkeypatch):
    # Temporarily set a formula as unapproved
    original = _FORMULA_REGISTRY["gross_margin"]
    unapproved = FormulaEntry(
        formula_id="gross_margin",
        version="1.0.0",
        display_name="Test",
        expression="test",
        unit="pct",
        approved=False,
    )
    monkeypatch.setitem(_FORMULA_REGISTRY, "gross_margin", unapproved)
    with pytest.raises(ValueError, match="is not approved"):
        get_formula("gross_margin")


def test_get_nonexistent_raises():
    with pytest.raises(ValueError, match="not found in registry"):
        get_formula("non_existent_formula_id_xyz")


def test_version_mismatch_raises():
    with pytest.raises(ValueError, match="version mismatch"):
        get_formula("gross_margin", version="2.0.0")


def test_list_approved_returns_at_least_5():
    approved = list_approved_formulas()
    assert len(approved) >= 5
    for entry in approved:
        assert entry.approved is True
        assert entry.approved_by is not None


def test_api_income_formulas_matches_registry():
    api_formulas = _income_formulas()
    assert len(api_formulas) == 7
    for item in api_formulas:
        assert "id" in item
        assert "name" in item
        assert "expression" in item
        assert "inputs" in item
        assert "unit" in item
        assert "version" in item

