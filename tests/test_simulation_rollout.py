from __future__ import annotations

from risk_dashboard.app.registry.registry import get_module_by_slug
from risk_dashboard.modules.pro_lab.module import module as pro_lab_module


def test_simulation_module_registration():
    mod = get_module_by_slug("simulation_lab")
    assert mod is not None
    assert mod.id == "simulation_lab"
    assert "module.simulation_lab.enabled" in mod.feature_flags
    assert "module.simulation_lab.multi_agent.enabled" in mod.feature_flags


def test_simulation_permission_scopes():
    scopes = set(pro_lab_module.permission_scopes)
    assert "pro_lab:strategy:read" in scopes
    assert "pro_lab:experiment:read" in scopes
    assert "pro_lab:run:read" in scopes
    assert "pro_lab:trade_detail:read" in scopes
    assert "pro_lab:run:propose" in scopes
    assert "pro_lab:run:execute" in scopes

