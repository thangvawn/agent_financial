import pandas as pd

from risk_dashboard.data.etl import align_mixed_frequency, weekly_volume_trend_pct


def test_align_mixed_frequency_merge_asof():
    daily = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-02-01"]),
            "vn_index": [100.0, 101.0, 102.0],
            "volume": [1e6, 1e6, 1e6],
        }
    )
    monthly = pd.DataFrame(
        {
            "period_end": pd.to_datetime(["2023-12-31", "2024-01-31"]),
            "usd_vnd_rate": [23000.0, 23500.0],
            "usd_vnd_1m_change_pct": [1.0, 2.0],
            "sbv_interest_rate_pct": [4.5, 4.5],
        }
    )
    out = align_mixed_frequency(daily, monthly)
    assert len(out) == 3
    assert out.loc[0, "usd_vnd_rate"] == 23000.0
    assert out.loc[2, "usd_vnd_rate"] == 23500.0


def test_weekly_volume_trend():
    vol = pd.Series([100.0] * 5 + [50.0] * 5)
    pct = weekly_volume_trend_pct(vol, window=5)
    assert pct < 0
