import json
from pathlib import Path

from risk_dashboard.modules.financials_product.application import build_company_financial_workspace
from risk_dashboard.schemas.financials import FinancialDataset


def _fixture_dataset() -> FinancialDataset:
    payload = json.loads((Path(__file__).parent / "fixtures" / "sample_financial_dataset.json").read_text())
    return FinancialDataset.model_validate(payload)


def test_company_workspace_exposes_one_complete_product_contract():
    workspace = build_company_financial_workspace(_fixture_dataset(), period_mode="quarter")

    assert workspace["schema_version"] == "2.0"
    assert workspace["company"]["ticker"] == "FPT"
    assert {item["key"] for item in workspace["headline_metrics"]} >= {"revenue", "net_income", "operating_cash_flow"}
    assert set(workspace["statements"]) == {"income", "balance", "cash_flow"}
    assert workspace["statements"]["income"]["periods"][-1] == "2025-Q4"
    assert workspace["quality"]["latest"]["free_cash_flow"] == 1_030_000_000_000
    assert workspace["data_provenance"]["coverage"]["total_periods"] == 5


def test_company_workspace_annualizes_flow_and_snapshot_fields():
    workspace = build_company_financial_workspace(_fixture_dataset(), period_mode="year")
    income = workspace["statements"]["income"]
    revenue = next(row for row in income["rows"] if row["key"] == "revenue")
    balance = workspace["statements"]["balance"]
    assets = next(row for row in balance["rows"] if row["key"] == "total_assets")

    assert income["periods"] == ["2024", "2025"]
    assert revenue["values"][-1]["value"] == 61_450_000_000_000
    assert assets["values"][-1]["value"] == 78_000_000_000_000


def test_company_workspace_prefers_lossless_provider_statement_rows():
    dataset = _fixture_dataset().model_copy(update={
        "raw_statements": {
            "balance": {
                "label": "Cân đối kế toán",
                "periods": ["2025-Q4", "2025-Q3"],
                "rows": [{
                    "key": "bsa1",
                    "label": "TÀI SẢN NGẮN HẠN",
                    "level": 0,
                    "is_group": True,
                    "emphasis": True,
                    "source": "reported",
                    "values": [
                        {"period": "2025-Q4", "value": 10_000},
                        {"period": "2025-Q3", "value": 9_000},
                    ],
                }],
            },
        },
    })

    workspace = build_company_financial_workspace(dataset, period_mode="quarter")

    assert workspace["statements"]["balance"]["rows"][0]["key"] == "bsa1"
    assert workspace["statements"]["balance"]["rows"][0]["is_group"] is True
    assert workspace["statements"]["balance"]["periods"] == ["2025-Q4", "2025-Q3"]
