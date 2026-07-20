from __future__ import annotations

import pandas as pd
from statsmodels.tsa.api import VAR

from risk_dashboard.schemas.snapshots import VarSummary


def _prep_var_df(panel: pd.DataFrame) -> pd.DataFrame:
    required = {"vn_index", "usd_vnd_rate", "sbv_interest_rate_pct"}
    missing = required - set(panel.columns)
    if missing:
        raise ValueError(f"panel missing columns: {missing}")
    out = pd.DataFrame(
        {
            "dl_vn": panel["vn_index"].pct_change(),
            "dl_fx": panel["usd_vnd_rate"].pct_change(),
            "dl_rate": panel["sbv_interest_rate_pct"].diff(),
        }
    ).dropna().reset_index(drop=True)
    return out


def fit_var_summary(panel: pd.DataFrame, maxlags: int = 4) -> VarSummary:
    data = _prep_var_df(panel)
    n_obs = len(data)
    if n_obs < maxlags + 10:
        return VarSummary(fitted=False, n_obs=n_obs, max_lag=maxlags, note="insufficient_obs")
    try:
        model = VAR(data)
        res = model.fit(maxlags=maxlags, ic="aic")
    except Exception as exc:  # pragma: no cover
        return VarSummary(fitted=False, n_obs=n_obs, max_lag=maxlags, note=f"var_error:{exc}")
    return VarSummary(
        fitted=True,
        n_obs=n_obs,
        max_lag=int(res.k_ar),
        note="ok",
    )


def var_impulse_note(panel: pd.DataFrame, maxlags: int = 4) -> str:
    summ = fit_var_summary(panel, maxlags=maxlags)
    if not summ.fitted:
        return "VAR không đủ dữ liệu ước lượng ổn định."
    return "VAR đa biến ước lượng được; kênh vĩ mô và chỉ số thị trường tương tác động."
