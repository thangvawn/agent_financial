import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.financials_product.application import build_practice_lab
from risk_dashboard.schemas.financials import FinancialDataset


def _fixture_dataset() -> FinancialDataset:
    payload = json.loads((Path(__file__).parent / "fixtures" / "sample_financial_dataset.json").read_text())
    return FinancialDataset.model_validate(payload)


def test_practice_lab_calculates_from_raw_data_and_ranks_companies():
    healthy = _fixture_dataset()
    weak = healthy.model_copy(
        deep=True,
        update={
            "ticker": "WEAK",
            "company_name": "Weak Company",
            "periods": [
                period.model_copy(
                    update={
                        "net_income": -abs(period.net_income or 0),
                        "operating_cash_flow": -abs(period.operating_cash_flow or 0),
                        "debt": (period.debt or 0) * 3,
                        "cash": (period.cash or 0) * 0.1,
                    }
                )
                for period in healthy.periods
            ],
        },
    )

    result = build_practice_lab([healthy, weak], period_mode="quarter")

    assert result["workflow"][0]["key"] == "raw"
    assert result["learning"]["estimated_minutes"] == 15
    assert [step["key"] for step in result["learning"]["steps"]] == ["frame", "explore", "compare", "reflect"]
    assert len(result["learning"]["reflection_prompts"]) == 3
    assert [item["ticker"] for item in result["ranking"]] == ["FPT", "WEAK"]
    fpt = next(item for item in result["companies"] if item["ticker"] == "FPT")
    cogs = next(item for item in fpt["calculated_fields"] if item["field"] == "cost_of_goods_sold")
    fcf = next(item for item in fpt["calculated_fields"] if item["field"] == "free_cash_flow")
    assert cogs["value"] == 10_400_000_000_000
    assert fcf["value"] == 1_030_000_000_000
    assert fpt["data_quality"]["revision_id"].startswith("rev_")
    assert fpt["overall"]["score"] > next(item for item in result["companies"] if item["ticker"] == "WEAK")["overall"]["score"]
    assert any(row["rank"] == 1 for row in result["comparison"]["metrics"][0]["rows"])


def test_practice_lab_does_not_impute_missing_raw_values():
    dataset = _fixture_dataset().model_copy(
        update={
            "ticker": "MISS",
            "periods": [
                _fixture_dataset().periods[0].model_copy(
                    update={"revenue": None, "gross_profit": None, "operating_cash_flow": None}
                )
            ],
        }
    )

    result = build_practice_lab([dataset])
    company = result["companies"][0]
    raw_revenue = next(item for item in company["raw_inputs"] if item["field"] == "revenue")
    derived_margin = next(item for item in company["calculated_fields"] if item["field"] == "gross_margin_pct")
    assert raw_revenue["value"] is None
    assert derived_margin["status"] == "insufficient_data"
    assert "revenue" in company["data_quality"]["missing_raw_fields"]


def test_practice_lab_rejects_dataset_without_periods():
    dataset = FinancialDataset(ticker="EMPTY", source="test", periods=[])
    with pytest.raises(ValueError, match="has no periods"):
        build_practice_lab([dataset])


def test_practice_lab_does_not_assign_rank_when_score_is_unavailable():
    dataset = FinancialDataset(
        ticker="NODATA",
        source="test",
        periods=[{"period": "2025-Q4", "year": 2025, "quarter": 4}],
    )
    result = build_practice_lab([dataset])
    assert result["companies"][0]["overall"]["score"] is None
    assert result["companies"][0]["overall"]["rank"] is None
    assert result["ranking"][0]["rank"] is None


def test_practice_lab_aligns_to_latest_common_period():
    first = _fixture_dataset()
    second = first.model_copy(
        update={
            "ticker": "OLDER",
            "periods": [period for period in first.periods if period.period != "2025-Q4"],
        }
    )
    result = build_practice_lab([first, second])
    assert result["controls"]["period"] == "2025-Q3"
    assert all(company["period"] == "2025-Q3" for company in result["companies"])
    assert result["warnings"] == []


def test_practice_lab_api_accepts_raw_datasets():
    client = TestClient(app)
    dataset = _fixture_dataset()
    response = client.post(
        "/financials/practice-lab",
        json={"datasets": [dataset.model_dump(mode="json")], "period_mode": "quarter"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["companies"][0]["ticker"] == "FPT"
    assert payload["companies"][0]["calculated_fields"]
    assert payload["errors"] == []
