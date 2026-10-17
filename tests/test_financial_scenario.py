import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from risk_dashboard.api.main import app
from risk_dashboard.modules.financials_product.application import build_financial_scenario
from risk_dashboard.schemas.financials import FinancialDataset, FinancialPeriodData


def _fixture_dataset() -> FinancialDataset:
    payload = json.loads((Path(__file__).parent / "fixtures" / "sample_financial_dataset.json").read_text())
    return FinancialDataset.model_validate(payload)


def test_scenario_keeps_reported_base_separate_and_projects_from_assumptions():
    result = build_financial_scenario(
        _fixture_dataset(),
        period="2025-Q4",
        revenue_growth_pct=5,
        gross_margin_pct=45,
        tax_rate_pct=20,
        operating_expense_growth_pct=3,
    )

    assert result["base"]["revenue"] == 16_800_000_000_000
    assert result["scenario"]["revenue"] == pytest.approx(17_640_000_000_000)
    assert result["scenario"]["gross_profit"] == pytest.approx(7_938_000_000_000)
    assert result["scenario"]["operating_profit"] == pytest.approx(4_899_500_000_000)
    assert result["scenario"]["net_income"] == pytest.approx(3_919_600_000_000)
    assert result["assumptions"]["gross_margin_pct"] == 45
    assert result["warnings"] == []


def test_scenario_does_not_impute_missing_operating_inputs():
    dataset = _fixture_dataset().model_copy(
        deep=True,
        update={
            "ticker": "MISS",
            "periods": [_fixture_dataset().periods[0].model_copy(update={"gross_profit": None})],
        },
    )
    result = build_financial_scenario(dataset)

    assert result["scenario"]["revenue"] is not None
    assert result["scenario"]["gross_profit"] is None
    assert result["scenario"]["operating_profit"] is None
    assert result["scenario"]["net_income"] is None
    assert len(result["warnings"]) >= 2


def test_scenario_converts_float_overflow_to_missing_with_warning():
    period = FinancialPeriodData(
        period="2025",
        year=2025,
        revenue=1.75e308,
        gross_profit=1.0e308,
        operating_profit=8.0e307,
        net_income=6.0e307,
    )
    dataset = FinancialDataset(ticker="HUGE", source="fixture", periods=[period])
    result = build_financial_scenario(dataset, revenue_growth_pct=5)

    assert result["scenario"]["revenue"] is None
    assert result["scenario"]["gross_profit"] is None
    assert result["scenario"]["net_income"] is None
    assert any("hữu hạn" in warning for warning in result["warnings"])


@pytest.mark.parametrize(
    "field,value",
    [("revenue_growth_pct", 501), ("gross_margin_pct", -1), ("tax_rate_pct", 101)],
)
def test_scenario_rejects_out_of_range_assumptions(field, value):
    assumptions = {field: value}
    with pytest.raises(ValueError):
        build_financial_scenario(_fixture_dataset(), **assumptions)


def test_scenario_api_returns_a_stable_contract_for_raw_dataset_cache():
    client = TestClient(app)
    # The endpoint resolves the configured provider/cache. This assertion only
    # runs when the fixture ticker is available in the local financial cache.
    response = client.post(
        "/financials/FPT/scenario",
        json={"period": "2025-Q4", "revenue_growth_pct": 5, "gross_margin_pct": 45},
    )
    if response.status_code == 503:
        pytest.skip("FPT provider/cache is unavailable in this environment")
    assert response.status_code == 200
    payload = response.json()
    assert {"base", "scenario", "assumptions", "formulas", "warnings"} <= payload.keys()


def test_financial_period_rejects_non_finite_amounts_and_invalid_quarter():
    with pytest.raises(ValidationError):
        FinancialPeriodData(period="2025-Q4", revenue=float("nan"))
    with pytest.raises(ValidationError):
        FinancialPeriodData(period="2025-Q5", quarter=5)
