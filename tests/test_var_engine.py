import pandas as pd

from risk_dashboard.engines.quant.var_engine import fit_var_summary


def test_var_insufficient_obs():
    df = pd.DataFrame(
        {
            "vn_index": [100, 101],
            "usd_vnd_rate": [23000, 23100],
            "sbv_interest_rate_pct": [4.5, 4.5],
        }
    )
    s = fit_var_summary(df)
    assert s.fitted is False


def test_var_fits_on_longer_panel(synthetic_panel):
    s = fit_var_summary(
        synthetic_panel[["vn_index", "usd_vnd_rate", "sbv_interest_rate_pct"]].copy()
    )
    assert s.fitted is True
