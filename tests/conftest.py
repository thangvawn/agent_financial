from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def synthetic_panel() -> pd.DataFrame:
    """Panel đủ dài để train XGBoost + VAR; tái lập được qua seed."""
    rng = np.random.default_rng(42)
    dates = pd.date_range("2015-01-01", periods=260, freq="B")
    n = len(dates)
    ret = rng.normal(0.0003, 0.012, n)
    vn = 500 * np.exp(np.cumsum(ret))
    vol = rng.lognormal(12, 0.25, n)
    fx = 20000 + np.cumsum(rng.normal(2, 4, n))
    sbv = 4.0 + np.cumsum(rng.normal(0, 0.02, n))
    usd_1m = rng.normal(0.5, 1.0, n)
    return pd.DataFrame(
        {
            "date": dates,
            "vn_index": vn,
            "volume": vol,
            "usd_vnd_rate": fx,
            "usd_vnd_1m_change_pct": usd_1m,
            "sbv_interest_rate_pct": sbv,
        }
    )


@pytest.fixture
def as_of_date(synthetic_panel: pd.DataFrame):
    return synthetic_panel["date"].iloc[-1].date()
