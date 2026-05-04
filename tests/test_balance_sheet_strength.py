import pytest

from risk_dashboard.quant.balance_sheet_strength import BalanceSheetDataError, build_balance_sheet_strength
from risk_dashboard.schemas.financials import FinancialDataset, FinancialPeriodData


def _dataset(**overrides) -> FinancialDataset:
    base = dict(
        period="2026-Q1",
        year=2026,
        quarter=1,
        total_assets=100_000_000_000,
        cash=15_000_000_000,
        receivables=20_000_000_000,
        inventory=10_000_000_000,
        fixed_assets=25_000_000_000,
        total_liabilities=42_000_000_000,
        current_liabilities=27_000_000_000,
        non_current_liabilities=15_000_000_000,
        short_term_debt=8_000_000_000,
        long_term_debt=12_000_000_000,
        equity=58_000_000_000,
        current_assets=60_000_000_000,
    )
    base.update(overrides)
    return FinancialDataset(ticker="TST", source="unit-test", periods=[FinancialPeriodData(**base)])


def test_balance_sheet_strength_full_data():
    response = build_balance_sheet_strength(_dataset())

    assert response.total_assets == 100
    assert response.total_funding == 100
    assert response.asset_items[0].percentage == 0.15
    assert response.funding_items[0].percentage == 0.27
    assert response.ratios.liabilities_to_assets == 0.42
    assert response.ratios.debt_to_equity == 0.3448


def test_missing_other_assets_is_estimated():
    response = build_balance_sheet_strength(_dataset())

    other = next(item for item in response.asset_items if item.key == "other_assets")
    assert other.value == 30
    assert "other_assets" in response.data_quality.estimated_fields


def test_missing_total_liabilities_is_estimated():
    response = build_balance_sheet_strength(_dataset(total_liabilities=None))

    assert response.ratios.liabilities_to_assets == 0.42
    assert "total_liabilities" in response.data_quality.estimated_fields


def test_consistency_warning_when_asset_buckets_gap():
    response = build_balance_sheet_strength(_dataset(
        other_assets=0,
        cash=10_000_000_000,
        receivables=10_000_000_000,
        inventory=10_000_000_000,
        fixed_assets=10_000_000_000,
    ))

    assert response.data_quality.consistency_warnings
    assert any(flag.code == "balance_sheet_mapping_gap" for flag in response.red_flags)


def test_high_liabilities_ratio_red_flag():
    response = build_balance_sheet_strength(_dataset(total_liabilities=70_000_000_000, current_liabilities=50_000_000_000, non_current_liabilities=20_000_000_000, equity=30_000_000_000))

    assert any(flag.code == "high_liabilities_ratio" for flag in response.red_flags)


def test_receivables_high_red_flag():
    response = build_balance_sheet_strength(_dataset(receivables=30_000_000_000))

    assert any(flag.code == "receivables_high" for flag in response.red_flags)


def test_total_assets_invalid():
    with pytest.raises(BalanceSheetDataError):
        build_balance_sheet_strength(_dataset(total_assets=0))
