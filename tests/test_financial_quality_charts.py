from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.quant.financial_quality_charts import (
    build_cash_flow_quality,
    build_financial_quality_charts,
    build_margin_analysis,
)
from risk_dashboard.schemas.financials import FinancialDataset, FinancialPeriodData


def _period(
    period: str,
    year: int,
    quarter: int,
    *,
    revenue: float = 1000,
    gross_profit: float = 400,
    operating_profit: float = 200,
    ebit: float | None = 180,
    net_income: float = 120,
    cfo: float = 150,
    cfi: float = -60,
    cff: float = -20,
    capex: float = 40,
    receivables: float = 180,
    inventory: float = 80,
) -> FinancialPeriodData:
    return FinancialPeriodData(
        period=period,
        year=year,
        quarter=quarter,
        revenue=revenue,
        gross_profit=gross_profit,
        operating_profit=operating_profit,
        ebit=ebit,
        net_income=net_income,
        operating_cash_flow=cfo,
        investing_cash_flow=cfi,
        financing_cash_flow=cff,
        capex=capex,
        receivables=receivables,
        inventory=inventory,
    )


def test_margin_chart_calculates_formulas_and_pp_changes():
    periods = [
        _period("2025-Q4", 2025, 4, revenue=1200, gross_profit=480, operating_profit=240, ebit=220, net_income=144),
        _period("2025-Q3", 2025, 3, revenue=1100, gross_profit=440, operating_profit=198, ebit=187, net_income=110),
        _period("2024-Q4", 2024, 4, revenue=1000, gross_profit=350, operating_profit=160, ebit=150, net_income=90),
    ]

    chart = build_margin_analysis(periods)
    latest = chart.latest

    assert latest.gross_margin_pct == 40
    assert latest.operating_margin_pct == 20
    assert latest.ebit_margin_pct == 18.33
    assert latest.net_margin_pct == 12
    assert latest.net_margin_yoy_pp == 3
    assert latest.net_margin_qoq_pp == 2
    assert "Net Margin" in chart.formulas["net_margin_pct"]
    assert chart.interpretation


def test_margin_chart_detects_red_flags():
    periods = [
        _period("2025-Q4", 2025, 4, revenue=1000, gross_profit=450, net_income=-20),
        _period("2025-Q3", 2025, 3, revenue=1000, gross_profit=420, net_income=30),
        _period("2025-Q2", 2025, 2, revenue=1000, gross_profit=410, net_income=60),
        _period("2025-Q1", 2025, 1, revenue=1000, gross_profit=400, net_income=90),
    ]

    chart = build_margin_analysis(periods)
    codes = {flag.code for flag in chart.flags}

    assert "net_margin_negative" in codes
    assert "margin_multi_period_decline" in codes


def test_cash_flow_chart_calculates_quality_metrics_and_score():
    periods = [
        _period("2025-Q4", 2025, 4, revenue=1000, net_income=100, cfo=130, cfi=-50, cff=-10, capex=40),
        _period("2024-Q4", 2024, 4, revenue=900, net_income=90, cfo=120, capex=35),
    ]

    chart = build_cash_flow_quality(periods)

    assert chart.latest.fcf == 90
    assert chart.latest.cfo_to_net_income == 1.3
    assert chart.latest.cfo_margin_pct == 13
    assert chart.latest.fcf_margin_pct == 9
    assert chart.latest.quality_score > 75
    assert "FCF =" in chart.formulas["fcf"]


def test_cash_flow_chart_detects_red_flags():
    periods = [
        _period("2025-Q4", 2025, 4, revenue=1000, net_income=100, cfo=-20, capex=30, receivables=260, inventory=160),
        _period("2025-Q3", 2025, 3, revenue=980, net_income=80, cfo=20, capex=50),
        _period("2024-Q4", 2024, 4, revenue=950, net_income=90, cfo=110, capex=40, receivables=150, inventory=90),
    ]

    chart = build_cash_flow_quality(periods)
    codes = {flag.code for flag in chart.flags}

    assert "positive_profit_negative_cfo" in codes
    assert "low_cfo_to_net_income" in codes
    assert "negative_fcf_streak" in codes
    assert "receivables_outgrow_revenue" in codes
    assert "inventory_outgrow_revenue" in codes
    assert chart.latest.quality_score < 55


def test_quality_charts_missing_data_handling():
    chart = build_financial_quality_charts(FinancialDataset(
        ticker="MISS",
        source="test",
        periods=[FinancialPeriodData(period="2025-Q4", year=2025, quarter=4)],
    ))

    assert "revenue" in chart.margin_analysis.missing_fields
    assert "operating_cash_flow" in chart.cash_flow_quality.missing_fields
    assert chart.margin_analysis.latest.net_margin_pct is None
    assert chart.cash_flow_quality.latest.quality_label in {"Theo dõi", "Cần kiểm tra", "Tốt"}


def test_quality_charts_api_shape(tmp_path, monkeypatch):
    from risk_dashboard.data.financials import import_financial_dataset

    monkeypatch.setenv("RISK_DASHBOARD_FINANCIALS_DIR", str(tmp_path / "financials"))
    import_financial_dataset(FinancialDataset(
        ticker="FQA",
        source="test",
        periods=[
            _period("2025-Q4", 2025, 4),
            _period("2024-Q4", 2024, 4),
        ],
    ))

    client = TestClient(app)
    response = client.get("/financials/FQA/quality-charts")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "FQA"
    assert "margin_analysis" in payload
    assert "cash_flow_quality" in payload
    assert payload["cash_flow_quality"]["latest"]["quality_score"] >= 0
