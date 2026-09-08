from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from risk_dashboard.data.financials import get_financial_dataset, save_financial_dataset
from risk_dashboard.schemas.financials import FinancialDataset, FinancialPeriodData


def test_bctc_cache_ttl_freshness(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("RISK_DASHBOARD_FINANCIALS_DIR", str(tmp_path / "financials"))
    
    # 1. Fresh dataset within TTL (1 hour ago)
    recent_time = datetime.now(timezone.utc) - timedelta(hours=1)
    dataset = FinancialDataset(
        ticker="VIC",
        source="vnstock_live",
        fetched_at=recent_time,
        periods=[FinancialPeriodData(period="2025-Q4", year=2025, quarter=4, revenue=100.0)],
    )
    save_financial_dataset(dataset)

    with patch("risk_dashboard.data.financials._attempt_vnstock_fetch") as mock_fetch:
        result = get_financial_dataset("VIC", max_cache_age_seconds=86400)
        assert result.ticker == "VIC"
        assert result.periods[0].revenue == 100.0
        mock_fetch.assert_not_called()


def test_bctc_cache_ttl_expiration_triggers_fetch(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("RISK_DASHBOARD_FINANCIALS_DIR", str(tmp_path / "financials"))

    # 2. Expired dataset older than 24 hours
    old_time = datetime.now(timezone.utc) - timedelta(hours=25)
    old_dataset = FinancialDataset(
        ticker="VNM",
        source="vnstock_live",
        fetched_at=old_time,
        periods=[FinancialPeriodData(period="2025-Q4", year=2025, quarter=4, revenue=200.0)],
    )
    save_financial_dataset(old_dataset)

    new_dataset = FinancialDataset(
        ticker="VNM",
        source="vnstock_live",
        fetched_at=datetime.now(timezone.utc),
        periods=[FinancialPeriodData(period="2025-Q4", year=2025, quarter=4, revenue=250.0)],
    )

    with patch("risk_dashboard.data.financials._attempt_vnstock_fetch", return_value=new_dataset) as mock_fetch:
        result = get_financial_dataset("VNM", max_cache_age_seconds=86400)
        assert result.periods[0].revenue == 250.0
        mock_fetch.assert_called_once_with("VNM")
