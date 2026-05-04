import json

import pandas as pd
from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.data.financials import _build_dataset_from_statement_frames
from risk_dashboard.quant.financial_analysis import analyze_financial_dataset
from risk_dashboard.schemas.financials import FinancialDataset


def _load_sample_dataset() -> FinancialDataset:
    with open("tests/fixtures/sample_financial_dataset.json", "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return FinancialDataset.model_validate(payload)


def test_analyze_financial_dataset_builds_snapshot():
    dataset = _load_sample_dataset()
    analysis = analyze_financial_dataset(dataset)

    assert analysis.ticker == "FPT"
    assert analysis.latest_period == "2025-Q4"
    assert analysis.summary.revenue is not None
    assert analysis.summary.revenue_growth_yoy_pct is not None
    assert analysis.summary.net_margin_pct is not None
    assert len(analysis.trends) >= 4
    assert analysis.highlights


def test_dupont_decomposition():
    dataset = _load_sample_dataset()
    analysis = analyze_financial_dataset(dataset)
    dupont = analysis.summary.dupont

    assert dupont is not None
    assert dupont.net_margin is not None and dupont.net_margin > 0
    assert dupont.asset_turnover is not None and dupont.asset_turnover > 0
    assert dupont.equity_multiplier is not None and dupont.equity_multiplier >= 1
    assert dupont.roe_decomposed is not None
    # DuPont ROE should roughly match direct ROE
    direct_roe = analysis.summary.roe_pct
    assert direct_roe is not None
    assert abs(dupont.roe_decomposed * 100 - direct_roe) < 0.01


def test_altman_z_score():
    dataset = _load_sample_dataset()
    analysis = analyze_financial_dataset(dataset)
    altman = analysis.summary.altman_z

    assert altman is not None
    assert altman.score is not None
    assert altman.zone in ("safe", "grey", "distress")
    assert len(altman.components) == 5
    # Quarterly data yields lower X3/X5, so "distress" zone is expected for single-quarter input
    assert altman.score > 0


def test_piotroski_f_score():
    dataset = _load_sample_dataset()
    analysis = analyze_financial_dataset(dataset)
    fscore = analysis.summary.piotroski_f

    assert fscore is not None
    assert fscore.score is not None
    assert 0 <= fscore.score <= 9
    assert len(fscore.details) == 9
    # FPT fixture is a healthy company — expect at least 4
    assert fscore.score >= 4


def test_health_radar_ranges():
    dataset = _load_sample_dataset()
    analysis = analyze_financial_dataset(dataset)
    radar = analysis.health_radar

    for field_name in ("profitability", "growth", "efficiency", "liquidity", "leverage", "cash_quality"):
        val = getattr(radar, field_name)
        assert 0 <= val <= 100, f"Radar {field_name}={val} out of [0,100]"


def test_ttm_aggregation():
    dataset = _load_sample_dataset()
    analysis = analyze_financial_dataset(dataset)
    s = analysis.summary

    assert s.revenue_ttm is not None
    assert s.net_income_ttm is not None
    assert s.ocf_ttm is not None
    # TTM = sum of 4 consecutive quarters (Q4+Q3+Q2+Q1 of 2025)
    q2025 = [p for p in dataset.periods if p.year == 2025]
    expected_rev = sum(p.revenue for p in q2025 if p.revenue is not None)
    assert abs(s.revenue_ttm - expected_rev) < 1


def test_roic_calculation():
    dataset = _load_sample_dataset()
    analysis = analyze_financial_dataset(dataset)
    assert analysis.summary.roic_pct is not None
    assert analysis.summary.roic_pct > 0


def test_advanced_flags_structure():
    dataset = _load_sample_dataset()
    analysis = analyze_financial_dataset(dataset)
    for flag in analysis.flags:
        assert flag.level in ("high", "medium", "low")
        assert flag.title
        assert flag.detail


def test_trend_includes_new_fields():
    dataset = _load_sample_dataset()
    analysis = analyze_financial_dataset(dataset)
    assert len(analysis.trends) >= 4
    first_trend = analysis.trends[0]
    assert first_trend.free_cash_flow is not None
    assert first_trend.operating_margin_pct is not None
    assert first_trend.roe_pct is not None


def test_yoy_reference_finds_correct_quarter():
    """YoY should find same quarter previous year, not adjacent quarter."""
    from risk_dashboard.quant.financial_analysis import _yoy_reference, _sort_periods
    from risk_dashboard.schemas.financials import FinancialPeriodData

    periods = _sort_periods([
        FinancialPeriodData(period="2025-Q4", year=2025, quarter=4, revenue=100),
        FinancialPeriodData(period="2025-Q3", year=2025, quarter=3, revenue=90),
        FinancialPeriodData(period="2024-Q4", year=2024, quarter=4, revenue=80),
        FinancialPeriodData(period="2024-Q3", year=2024, quarter=3, revenue=70),
    ])
    current = periods[0]  # 2025-Q4
    ref = _yoy_reference(periods, current)
    assert ref is not None
    assert ref.period == "2024-Q4"


def test_yoy_reference_returns_none_when_no_match():
    from risk_dashboard.quant.financial_analysis import _yoy_reference, _sort_periods
    from risk_dashboard.schemas.financials import FinancialPeriodData

    periods = _sort_periods([
        FinancialPeriodData(period="2025-Q4", year=2025, quarter=4, revenue=100),
        FinancialPeriodData(period="2025-Q3", year=2025, quarter=3, revenue=90),
    ])
    ref = _yoy_reference(periods, periods[0])
    assert ref is None


def test_ttm_requires_consecutive_quarters():
    from risk_dashboard.quant.financial_analysis import _ttm_sum, _sort_periods
    from risk_dashboard.schemas.financials import FinancialPeriodData

    # Missing Q2 — TTM should return None
    periods = _sort_periods([
        FinancialPeriodData(period="2025-Q4", year=2025, quarter=4, revenue=100),
        FinancialPeriodData(period="2025-Q3", year=2025, quarter=3, revenue=90),
        FinancialPeriodData(period="2025-Q1", year=2025, quarter=1, revenue=70),
        FinancialPeriodData(period="2024-Q4", year=2024, quarter=4, revenue=80),
    ])
    assert _ttm_sum(periods, "revenue") is None


def test_roic_none_when_invested_capital_negative():
    """ROIC should be None when equity+debt-cash <= 0."""
    from risk_dashboard.schemas.financials import FinancialPeriodData
    from risk_dashboard.quant.financial_analysis import _build_snapshot

    p = FinancialPeriodData(
        period="2025-Q4", year=2025, quarter=4,
        revenue=1000, gross_profit=400, operating_profit=200, net_income=150,
        total_assets=2000, total_liabilities=800, equity=100,
        cash=600, debt=50,  # IC = 100 + 50 - 600 = -450
        current_assets=900, current_liabilities=500,
        operating_cash_flow=200, capex=80,
    )
    snapshot = _build_snapshot(p, None, [p])
    assert snapshot.roic_pct is None


def test_altman_z_skipped_for_bank():
    from risk_dashboard.schemas.financials import FinancialDataset, FinancialPeriodData

    ds = FinancialDataset(
        ticker="VCB", source="test", industry="Ngân hàng",
        periods=[
            FinancialPeriodData(
                period="2025-Q4", year=2025, quarter=4,
                revenue=50000, net_income=10000,
                total_assets=2000000, equity=200000,
                current_assets=500000, current_liabilities=400000,
            ),
        ],
    )
    analysis = analyze_financial_dataset(ds)
    assert analysis.summary.altman_z is not None
    assert analysis.summary.altman_z.score is None
    assert analysis.summary.altman_z.zone is None


def test_financial_import_and_analysis_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setenv("RISK_DASHBOARD_FINANCIALS_DIR", str(tmp_path / "financials"))
    dataset = _load_sample_dataset()
    client = TestClient(app)

    imported = client.post("/financials/import", json={"dataset": dataset.model_dump(mode="json")})
    assert imported.status_code == 200
    assert imported.json()["ok"] is True
    assert imported.json()["periods"] == len(dataset.periods)

    fetched = client.get("/financials/FPT/analysis")
    assert fetched.status_code == 200
    payload = fetched.json()

    assert payload["ticker"] == "FPT"
    assert payload["latest_period"] == "2025-Q4"
    assert payload["summary"]["revenue"] == dataset.periods[0].revenue
    assert "highlights" in payload


def test_financial_status_endpoint():
    client = TestClient(app)
    response = client.get("/financials/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "vnstock-live"
    assert "notes" in payload


def test_build_dataset_from_vnstock_row_oriented_frames():
    income_df = pd.DataFrame(
        [
            {
                "CP": "FPT",
                "Năm": 2025,
                "Kỳ": 4,
                "Tăng trưởng doanh thu (%)": 0.15,
                "Doanh thu thuần": 1000,
                "Lãi gộp": 420,
                "Lãi/Lỗ từ hoạt động kinh doanh": 180,
                "Lợi nhuận sau thuế của Cổ đông công ty mẹ (đồng)": 150,
            }
        ]
    )
    balance_df = pd.DataFrame(
        [
            {
                "CP": "FPT",
                "Năm": 2025,
                "Kỳ": 4,
                "TÀI SẢN NGẮN HẠN (đồng)": 900,
                "Tiền và tương đương tiền (đồng)": 220,
                "Các khoản phải thu ngắn hạn (đồng)": 180,
                "Hàng tồn kho ròng": 90,
                "TỔNG CỘNG TÀI SẢN (đồng)": 2000,
                "Nợ ngắn hạn (đồng)": 500,
                "NỢ PHẢI TRẢ (đồng)": 800,
                "VỐN CHỦ SỞ HỮU (đồng)": 1200,
                "Vay và nợ thuê tài chính ngắn hạn (đồng)": 140,
                "Vay và nợ thuê tài chính dài hạn (đồng)": 260,
            }
        ]
    )
    cashflow_df = pd.DataFrame(
        [
            {
                "CP": "FPT",
                "Năm": 2025,
                "Kỳ": 4,
                "Lưu chuyển tiền tệ ròng từ các hoạt động SXKD": 210,
                "Lưu chuyển từ hoạt động đầu tư": -120,
                "Lưu chuyển tiền từ hoạt động tài chính": -45,
                "Mua sắm TSCĐ": -80,
            }
        ]
    )

    dataset = _build_dataset_from_statement_frames(
        "FPT",
        income_df=income_df,
        balance_df=balance_df,
        cashflow_df=cashflow_df,
        source="vnstock-vci",
    )

    assert dataset.source == "vnstock-vci"
    assert len(dataset.periods) == 1
    period = dataset.periods[0]
    assert period.period == "2025-Q4"
    assert period.revenue == 1000
    assert period.gross_profit == 420
    assert period.operating_profit == 180
    assert period.net_income == 150
    assert period.total_assets == 2000
    assert period.total_liabilities == 800
    assert period.equity == 1200
    assert period.current_assets == 900
    assert period.current_liabilities == 500
    assert period.cash == 220
    assert period.receivables == 180
    assert period.inventory == 90
    assert period.debt == 400
    assert period.operating_cash_flow == 210
    assert period.investing_cash_flow == -120
    assert period.financing_cash_flow == -45
    assert period.capex == -80
