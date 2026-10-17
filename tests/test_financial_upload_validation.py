from __future__ import annotations

from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.data.financials import load_cached_financial_dataset


def _upload_and_analyze(client: TestClient, csv_payload: str):
    uploaded = client.post(
        "/financials/upload",
        data={"ticker": "EDU"},
        files={"file": ("edu-bctc.csv", csv_payload.encode("utf-8"), "text/csv")},
    )
    assert uploaded.status_code == 200, uploaded.text
    upload_id = uploaded.json()["upload_id"]
    return client.post(f"/financials/uploads/{upload_id}/analyze")


def test_csv_upload_keeps_blank_amounts_missing_and_parses_common_formats(tmp_path, monkeypatch):
    monkeypatch.setenv("RISK_DASHBOARD_FINANCIALS_DIR", str(tmp_path / "financials"))
    monkeypatch.setenv("RISK_DASHBOARD_FINANCIAL_UPLOADS_DIR", str(tmp_path / "uploads"))
    client = TestClient(app)
    response = _upload_and_analyze(
        client,
        "CP,Năm,Kỳ,Doanh thu thuần,Lợi nhuận sau thuế,TỔNG CỘNG TÀI SẢN\n"
        'EDU,2025,Q4,,"(1.234,5)",2.000\n',
    )

    assert response.status_code == 200, response.text
    dataset = load_cached_financial_dataset("EDU")
    assert dataset is not None
    period = dataset.periods[0]
    assert period.revenue is None
    assert period.net_income == -1234.5
    assert period.total_assets == 2000
    assert period.quarter == 4


def test_csv_upload_rejects_malformed_numbers_and_duplicate_periods(tmp_path, monkeypatch):
    monkeypatch.setenv("RISK_DASHBOARD_FINANCIALS_DIR", str(tmp_path / "financials"))
    monkeypatch.setenv("RISK_DASHBOARD_FINANCIAL_UPLOADS_DIR", str(tmp_path / "uploads"))
    client = TestClient(app)

    malformed = _upload_and_analyze(
        client,
        "CP,Năm,Kỳ,Doanh thu thuần\nEDU,2025,4,not-a-number\n",
    )
    assert malformed.status_code == 422
    assert "not-a-number" in str(malformed.json()["detail"])

    duplicate = _upload_and_analyze(
        client,
        "CP,Năm,Kỳ,Doanh thu thuần\nEDU,2025,4,100\nEDU,2025,Q4,110\n",
    )
    assert duplicate.status_code == 422
    assert "bị lặp" in str(duplicate.json()["detail"])


def test_matrix_csv_upload_maps_metric_rows_to_periods(tmp_path, monkeypatch):
    monkeypatch.setenv("RISK_DASHBOARD_FINANCIALS_DIR", str(tmp_path / "financials"))
    monkeypatch.setenv("RISK_DASHBOARD_FINANCIAL_UPLOADS_DIR", str(tmp_path / "uploads"))
    response = _upload_and_analyze(
        TestClient(app),
        "metric,2023,2024,2025\n"
        "Revenue,100,120,150\n"
        "Gross Profit,40,48,60\n"
        "Net Income,10,12,15\n",
    )

    assert response.status_code == 200, response.text
    dataset = load_cached_financial_dataset("EDU")
    assert dataset is not None
    assert [period.period for period in dataset.periods] == ["2023", "2024", "2025"]
    assert dataset.periods[-1].revenue == 150
    assert dataset.periods[-1].gross_profit == 60
    assert dataset.periods[-1].net_income == 15


def test_non_csv_analysis_does_not_create_fabricated_periods(tmp_path, monkeypatch):
    monkeypatch.setenv("RISK_DASHBOARD_FINANCIAL_UPLOADS_DIR", str(tmp_path / "uploads"))
    client = TestClient(app)
    uploaded = client.post(
        "/financials/upload",
        data={"ticker": "EDU"},
        files={"file": ("edu-bctc.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert uploaded.status_code == 200
    analyzed = client.post(f"/financials/uploads/{uploaded.json()['upload_id']}/analyze")
    assert analyzed.status_code == 501
    assert "chưa được triển khai" in analyzed.json()["detail"]
