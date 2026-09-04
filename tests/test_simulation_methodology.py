from __future__ import annotations

from risk_dashboard.modules.pro_lab.domain.methodology_checks import (
    check_benchmark_mismatch,
    check_look_ahead_bias,
    check_overfitting_risk,
    check_survivorship_bias,
    check_transaction_costs,
    run_all_methodology_checks,
)
from risk_dashboard.modules.pro_lab.schemas.simulation_agent import ReproducibilityManifest


def _make_base_manifest(**kwargs) -> ReproducibilityManifest:
    defaults = {
        "schema_version": "1.0.0",
        "strategy_id": "strat_test",
        "strategy_version": "1.0.0",
        "dataset_source": "cafef_eod",
        "dataset_version": "v2024.1",
        "data_start": "2021-01-01",
        "data_end": "2023-12-31",
        "parameters": {"lookback": 20},
        "commission_pct": 0.15,
        "slippage_pct": 0.20,
        "benchmark": "VNINDEX",
        "engine_version": "1.0.0",
        "execution_timestamp": "2026-09-02T12:00:00Z",
        "metrics_calculation_version": "1.0.0",
    }
    defaults.update(kwargs)
    return ReproducibilityManifest(**defaults)


def test_look_ahead_bias_detection():
    # Clean manifest
    m_clean = _make_base_manifest()
    assert len(check_look_ahead_bias(m_clean)) == 0

    # Flawed manifest
    m_flawed = _make_base_manifest(parameters={"execute_on_same_bar_close": True})
    issues = check_look_ahead_bias(m_flawed)
    assert len(issues) == 1
    assert "Look-ahead bias" in issues[0]


def test_survivorship_bias_detection():
    # Old period with VN30 fixed constituents
    m_old_vn30 = _make_base_manifest(data_start="2015-01-01", benchmark="VN30")
    issues = check_survivorship_bias(m_old_vn30)
    assert len(issues) == 1
    assert "Survivorship bias" in issues[0]

    # Recent period
    m_recent = _make_base_manifest(data_start="2022-01-01", benchmark="VN30")
    assert len(check_survivorship_bias(m_recent)) == 0


def test_overfitting_risk_detection():
    # Many parameters
    m_many_params = _make_base_manifest(
        parameters={f"param_{i}": i for i in range(12)}
    )
    issues = check_overfitting_risk(m_many_params, run_count=1)
    assert len(issues) == 1
    assert "quá nhiều tham số" in issues[0]

    # Multiple testing run count
    m_normal = _make_base_manifest()
    issues_runs = check_overfitting_risk(m_normal, run_count=20)
    assert len(issues_runs) == 1
    assert "Multiple Testing" in issues_runs[0]


def test_transaction_costs_detection():
    # 0 commission
    m_zero_fee = _make_base_manifest(commission_pct=0.0)
    issues = check_transaction_costs(m_zero_fee)
    assert any("Thiếu phí giao dịch" in s for s in issues)

    # 0 slippage
    m_zero_slip = _make_base_manifest(slippage_pct=0.0)
    issues_slip = check_transaction_costs(m_zero_slip)
    assert any("Thiếu trượt giá" in s for s in issues_slip)


def test_benchmark_mismatch_detection():
    m = _make_base_manifest(benchmark="VNINDEX")
    issues = check_benchmark_mismatch(m, run_benchmark="VN30")
    assert len(issues) == 1
    assert "Mâu thuẫn benchmark" in issues[0]

    issues_ok = check_benchmark_mismatch(m, run_benchmark="VNINDEX")
    assert len(issues_ok) == 0



def test_run_all_methodology_checks():
    m_all_flaws = _make_base_manifest(
        data_start="2015-01-01",
        benchmark="VN30",
        commission_pct=0.0,
        slippage_pct=0.0,
        parameters={"execute_on_same_bar_close": True, **{f"p_{i}": i for i in range(10)}},
    )
    all_issues = run_all_methodology_checks(m_all_flaws, run_count=25)
    assert len(all_issues) >= 5
