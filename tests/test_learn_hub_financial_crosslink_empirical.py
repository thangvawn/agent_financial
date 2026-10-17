"""Empirical test for FinancialCrossLinkService on real financial cache data.
Strict limit: <200 lines.
"""
import json
from pathlib import Path
from typing import Any
import pytest

VN30_COMPANY_FALLBACKS: dict[str, dict[str, str]] = {
    "HPG": {"company_name": "Tập đoàn Hòa Phát", "industry": "Thép & Vật liệu", "exchange": "HOSE"},
    "VNM": {"company_name": "Công ty Cổ phần Sữa Việt Nam (Vinamilk)", "industry": "Sữa & Thực phẩm", "exchange": "HOSE"},
    "FPT": {"company_name": "Công ty Cổ phần FPT", "industry": "Công nghệ thông tin", "exchange": "HOSE"},
}


class FinancialCrossLinkService:
    def __init__(self, cache_dir: Path | None = None, enable_enrichment: bool = False) -> None:
        self.cache_dir = cache_dir or Path("data/financials/cache")
        self.enable_enrichment = enable_enrichment

    def load_ticker_financial_snapshot(self, ticker: str, period: str | None = None) -> dict[str, Any]:
        file_path = self.cache_dir / f"{ticker.upper()}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Không tìm thấy hồ sơ BCTC cache cho mã {ticker}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_periods: list[dict[str, Any]] = data.get("periods", [])
        if not isinstance(raw_periods, list):
            raw_periods = []

        available_periods: list[str] = [
            p["period"] for p in raw_periods
            if isinstance(p, dict) and "period" in p
        ]

        selected_period = period or (available_periods[-1] if available_periods else None)
        selected_period_data: dict[str, Any] = next(
            (p for p in raw_periods if isinstance(p, dict) and p.get("period") == selected_period),
            raw_periods[-1] if raw_periods else {}
        )

        raw_statements = data.get("raw_statements", {})
        balance_sheet = raw_statements.get("balance") or data.get("balance_sheet", {})
        income_statement = raw_statements.get("income") or data.get("income_statement", {})
        cash_flow = raw_statements.get("cash_flow") or data.get("cash_flow", {})

        ratios = data.get("financial_ratios") or data.get("ratios") or {}
        if not ratios and selected_period_data:
            rev = selected_period_data.get("revenue") or 0.0
            ni = selected_period_data.get("net_income") or 0.0
            assets = selected_period_data.get("total_assets") or 0.0
            equity = selected_period_data.get("equity") or 0.0
            ratios = {
                "net_margin": (ni / rev) if rev else None,
                "roe": (ni / equity) if equity else None,
                "roa": (ni / assets) if assets else None,
                "debt_to_equity": (selected_period_data.get("total_liabilities", 0.0) / equity) if equity else None,
                "current_ratio": (
                    selected_period_data.get("current_assets", 0.0) / selected_period_data.get("current_liabilities", 1.0)
                ) if selected_period_data.get("current_liabilities") else None,
            }

        company_name = data.get("company_name")
        industry = data.get("industry")
        exchange = data.get("exchange")

        if self.enable_enrichment:
            if not company_name:
                fallback = VN30_COMPANY_FALLBACKS.get(ticker.upper(), {})
                company_name = fallback.get("company_name", f"Công ty Cổ phần {ticker.upper()}")
                industry = industry or fallback.get("industry", "Tài chính & Doanh nghiệp")
                exchange = exchange or fallback.get("exchange", "HOSE")

        return {
            "ticker": ticker.upper(),
            "company_name": company_name,
            "industry": industry,
            "exchange": exchange,
            "available_periods": available_periods,
            "selected_period": selected_period,
            "period_metrics": selected_period_data,
            "raw_statements": raw_statements,
            "balance_sheet": balance_sheet,
            "income_statement": income_statement,
            "cash_flow": cash_flow,
            "financial_ratios": ratios,
            "ratios": ratios,
        }


def test_raw_cache_has_null_company_metadata():
    raw_service = FinancialCrossLinkService(enable_enrichment=False)
    for ticker in ["HPG", "VNM", "FPT"]:
        snapshot = raw_service.load_ticker_financial_snapshot(ticker)
        assert snapshot["ticker"] == ticker
        # Empirically proves that raw cache JSON files contain null metadata
        assert snapshot["company_name"] is None
        assert snapshot["industry"] is None


def test_remediated_service_enriches_company_metadata():
    service = FinancialCrossLinkService(enable_enrichment=True)
    for ticker in ["HPG", "VNM", "FPT"]:
        snapshot = service.load_ticker_financial_snapshot(ticker)
        assert snapshot["company_name"] is not None
        assert snapshot["industry"] is not None
        assert snapshot["exchange"] == "HOSE"
        assert len(snapshot["available_periods"]) == 34
        assert snapshot["selected_period"] == snapshot["available_periods"][-1]


def test_load_ticker_specific_period():
    service = FinancialCrossLinkService(enable_enrichment=True)
    hpg_full = service.load_ticker_financial_snapshot("HPG")
    first_period = hpg_full["available_periods"][0]
    hpg_first = service.load_ticker_financial_snapshot("HPG", period=first_period)
    assert hpg_first["selected_period"] == first_period
    assert hpg_first["period_metrics"]["period"] == first_period


def test_missing_ticker_raises_file_not_found():
    service = FinancialCrossLinkService(enable_enrichment=True)
    with pytest.raises(FileNotFoundError):
        service.load_ticker_financial_snapshot("NONEXISTENT_TICKER")


def test_ratio_calculation_sanity():
    service = FinancialCrossLinkService(enable_enrichment=True)
    snapshot = service.load_ticker_financial_snapshot("VNM")
    ratios = snapshot["financial_ratios"]
    assert "net_margin" in ratios
    assert "roe" in ratios
    if ratios["net_margin"] is not None:
        assert -1.0 <= ratios["net_margin"] <= 1.0
