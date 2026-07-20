import json

import pandas as pd
from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.data.financials import _build_dataset_from_statement_frames
from risk_dashboard.engines.quant.financial_analysis import analyze_financial_dataset
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
    from risk_dashboard.engines.quant.financial_analysis import _yoy_reference, _sort_periods
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
    from risk_dashboard.engines.quant.financial_analysis import _yoy_reference, _sort_periods
    from risk_dashboard.schemas.financials import FinancialPeriodData

    periods = _sort_periods([
        FinancialPeriodData(period="2025-Q4", year=2025, quarter=4, revenue=100),
        FinancialPeriodData(period="2025-Q3", year=2025, quarter=3, revenue=90),
    ])
    ref = _yoy_reference(periods, periods[0])
    assert ref is None


def test_ttm_requires_consecutive_quarters():
    from risk_dashboard.engines.quant.financial_analysis import _ttm_sum, _sort_periods
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
    from risk_dashboard.engines.quant.financial_analysis import _build_snapshot

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


def test_financial_sections_endpoints_return_tab_payloads(tmp_path, monkeypatch):
    monkeypatch.setenv("RISK_DASHBOARD_FINANCIALS_DIR", str(tmp_path / "financials"))
    dataset = _load_sample_dataset()
    client = TestClient(app)

    imported = client.post("/financials/import", json={"dataset": dataset.model_dump(mode="json")})
    assert imported.status_code == 200

    sections = client.get("/financials/FPT/sections")
    assert sections.status_code == 200
    payload = sections.json()
    section_ids = [item["section"] for item in payload["sections"]]
    assert section_ids == [
        "overview",
        "income_statement",
        "balance_sheet",
        "cash_flow",
        "ratios",
        "horizontal_analysis",
        "vertical_analysis",
        "risk_alerts",
        "report",
    ]

    overview = client.get("/financials/FPT/sections/overview")
    assert overview.status_code == 200
    assert overview.json()["company"]["ticker"] == "FPT"

    income = client.get("/financials/FPT/sections/ket-qua-kinh-doanh")
    assert income.status_code == 200
    assert income.json()["section"] == "income_statement"
    assert income.json()["table"]

    invalid = client.get("/financials/FPT/sections/not-a-section")
    assert invalid.status_code == 404


def test_financial_cockpit_returns_page_ready_payload(tmp_path, monkeypatch):
    monkeypatch.setenv("RISK_DASHBOARD_FINANCIALS_DIR", str(tmp_path / "financials"))
    dataset = _load_sample_dataset()
    client = TestClient(app)

    imported = client.post("/financials/import", json={"dataset": dataset.model_dump(mode="json")})
    assert imported.status_code == 200

    response = client.get("/financials/FPT/cockpit")
    assert response.status_code == 200
    payload = response.json()

    assert payload["ticker"] == "FPT"
    assert payload["company"]["latest_period"] == "2025-Q4"
    assert len(payload["headline_kpis"]) == 6
    assert {"data_quality", "narrative", "charts", "statement_tables", "risk_flags"} <= set(payload)
    assert payload["charts"]["revenue_income_trend"]["points"]
    assert payload["statement_tables"]["income"]["rows"]
    assert "missing_by_group" in payload["data_quality"]
    assert payload["source_evidence"] == []


def test_bctc_income_statement_educational_apis(tmp_path, monkeypatch):
    monkeypatch.setenv("RISK_DASHBOARD_FINANCIALS_DIR", str(tmp_path / "financials"))
    monkeypatch.setenv("RISK_DASHBOARD_APP_STATE_DB", str(tmp_path / "app_state.db"))
    dataset = _load_sample_dataset()
    client = TestClient(app)

    imported = client.post("/financials/import", json={"dataset": dataset.model_dump(mode="json")})
    assert imported.status_code == 200

    overview = client.get(
        "/api/bctc/income-statement/overview",
        params={"company_id": "FPT", "period": "2025-Q4", "compare_with": "same_period_last_year"},
    )
    assert overview.status_code == 200
    overview_payload = overview.json()
    kpis = {item["key"]: item for item in overview_payload["kpis"]}
    assert {"revenue", "gross_profit", "ebit", "net_profit", "gross_margin", "net_margin"} <= set(kpis)
    assert kpis["gross_margin"]["formula"]["id"] == "gross_margin"
    assert kpis["gross_margin"]["calculation_status"] == "ok"
    assert kpis["revenue"]["evidence"]["current_period"] == "2025-Q4"
    assert "khuyến nghị" in overview_payload["disclaimer"].lower()

    table = client.get("/api/bctc/income-statement/table", params={"company_id": "FPT"})
    assert table.status_code == 200
    assert table.json()["rows"]

    trends = client.get("/api/bctc/income-statement/trends", params={"company_id": "FPT", "metrics": "revenue,net_profit"})
    assert trends.status_code == 200
    assert trends.json()["points"]
    assert set(trends.json()["points"][-1]) <= {"period", "year", "quarter", "revenue", "net_profit"}

    formulas = client.get("/api/bctc/income-statement/formulas")
    assert formulas.status_code == 200
    assert any(item["id"] == "net_margin" for item in formulas.json()["formulas"])

    explain = client.get(
        "/api/bctc/income-statement/explain-line-item",
        params={"line_item_key": "revenue", "student_level": "beginner"},
    )
    assert explain.status_code == 200
    assert explain.json()["learning_questions"]

    insights = client.get("/api/bctc/income-statement/insights", params={"company_id": "FPT", "period": "2025-Q4"})
    assert insights.status_code == 200
    assert all({"rule_id", "message", "severity", "evidence_json"} <= set(item) for item in insights.json()["insights"])

    questions = client.get("/api/bctc/income-statement/questions", params={"company_id": "FPT", "student_level": "advanced"})
    assert questions.status_code == 200
    assert len(questions.json()["learning_flow"]) == 8

    note = client.post(
        "/api/bctc/income-statement/student-notes",
        json={
            "student_id": "student-1",
            "company_id": "FPT",
            "period": "2025-Q4",
            "note_content": "Doanh thu tăng, cần kiểm tra thêm biên lợi nhuận và giá vốn.",
            "related_metrics": ["revenue", "gross_margin"],
        },
    )
    assert note.status_code == 200
    assert note.json()["ok"] is True
    assert note.json()["note_id"].startswith("income-note-")

    review = client.get(
        "/api/bctc/income-statement/instructor-review",
        params={"company_id": "FPT", "period": "2025-Q4"},
    )
    assert review.status_code == 200
    assert review.json()["note_count"] == 1
    assert review.json()["notes"][0]["student_id"] == "student-1"


def test_financial_status_endpoint():
    client = TestClient(app)
    response = client.get("/financials/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "vnstock-live"


def test_financial_upload_accepts_supported_bctc_files(tmp_path, monkeypatch):
    monkeypatch.setenv("RISK_DASHBOARD_FINANCIALS_DIR", str(tmp_path / "financials"))
    monkeypatch.setenv("RISK_DASHBOARD_FINANCIAL_UPLOADS_DIR", str(tmp_path / "uploads"))
    client = TestClient(app)

    supported = client.get("/financials/upload/supported-types")
    assert supported.status_code == 200
    assert ".pdf" in supported.json()["accept"]
    assert ".xlsx" in supported.json()["accept"]

    response = client.post(
        "/financials/upload",
        data={"ticker": "FPT", "report_type": "auto", "period": "2025-Q4"},
        files={"file": ("fpt-q4.pdf", b"%PDF-1.4\nsample bctc", "application/pdf")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "uploaded"
    assert payload["ticker"] == "FPT"
    assert payload["file_type"]["extension"] == ".pdf"
    assert payload["file_type"]["pipeline"] == "pdf_text_or_ocr"
    assert payload["upload_id"].startswith("bctc-")

    rejected = client.post(
        "/financials/upload",
        files={"file": ("readme.exe", b"nope", "application/octet-stream")},
    )
    assert rejected.status_code == 415


def test_financial_upload_csv_can_be_analyzed_into_dataset(tmp_path, monkeypatch):
    monkeypatch.setenv("RISK_DASHBOARD_FINANCIALS_DIR", str(tmp_path / "financials"))
    monkeypatch.setenv("RISK_DASHBOARD_FINANCIAL_UPLOADS_DIR", str(tmp_path / "uploads"))
    client = TestClient(app)
    csv_payload = (
        "CP,Năm,Kỳ,Doanh thu thuần,Lợi nhuận sau thuế,TỔNG CỘNG TÀI SẢN,"
        "NỢ PHẢI TRẢ,VỐN CHỦ SỞ HỮU,Lưu chuyển tiền tệ ròng từ các hoạt động SXKD\n"
        "FPT,2025,4,1000,150,2000,800,1200,210\n"
        "FPT,2024,4,900,120,1800,760,1040,180\n"
    )

    upload = client.post(
        "/financials/upload",
        data={"ticker": "FPT"},
        files={"file": ("fpt-bctc.csv", csv_payload.encode("utf-8"), "text/csv")},
    )
    assert upload.status_code == 200

    analyzed = client.post(f"/financials/uploads/{upload.json()['upload_id']}/analyze")
    assert analyzed.status_code == 200
    payload = analyzed.json()
    assert payload["ok"] is True
    assert payload["ticker"] == "FPT"
    assert payload["periods"] == 2
    assert payload["analysis"]["summary"]["revenue"] == 1000
    assert payload["upload"]["status"] == "analyzed"
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
