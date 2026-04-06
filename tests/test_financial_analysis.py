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
