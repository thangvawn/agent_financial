from datetime import date
from unittest.mock import patch

import pandas as pd

from risk_dashboard.data.macro_auto import AutoMacroSource, _annual_value_for_year, _map_annual_to_month_ends


def test_annual_value_for_year():
    df = pd.DataFrame({"year": [2022, 2023], "value": [3.0, 4.0]})
    assert _annual_value_for_year(df, 2023) == 4.0
    assert _annual_value_for_year(df, 2024) == 4.0


def test_auto_macro_source_mocked():
    fx = pd.DataFrame(
        {
            "period_end": pd.to_datetime(["2024-01-31", "2024-02-29"]),
            "usd_vnd_rate": [25000.0, 25100.0],
            "usd_vnd_1m_change_pct": [0.0, 0.4],
        }
    )
    inf = pd.DataFrame({"year": [2023, 2024], "value": [3.1, 3.5]})
    lend = pd.DataFrame({"year": [2023, 2024], "value": [8.0, 8.5]})
    fdi = pd.DataFrame({"year": [2022, 2023, 2024], "value": [1e9, 1.1e9, 1.2e9]})

    with patch("risk_dashboard.data.macro_auto._fetch_usd_vnd_monthly_yfinance", return_value=fx):
        with patch(
            "risk_dashboard.data.macro_auto._wb_fetch_indicator",
            side_effect=[inf, lend, fdi],
        ):
            src = AutoMacroSource()
            out = src.load_macro_monthly(date(2024, 1, 1), date(2024, 2, 29))

    assert len(out) == 2
    assert "sbv_interest_rate_pct" in out.columns
    assert out["cpi_yoy_pct"].notna().all()


def test_map_annual_to_month_ends():
    df = pd.DataFrame({"year": [2024], "value": [5.0]})
    idx = pd.to_datetime(["2024-01-31", "2024-02-29"])
    s = _map_annual_to_month_ends(df, idx)
    assert (s == 5.0).all()
