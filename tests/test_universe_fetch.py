from datetime import date

import pandas as pd

from risk_dashboard.data.market_connector import DataFrameMarketSource
from risk_dashboard.data.universe_fetch import extract_vn30_tickers


def test_extract_vn30_tickers_returns_sorted_unique_values():
    listings = pd.DataFrame(
        {
            "ticker": ["VCB", "ACB", "VCB", "SSI", None],
            "VN30": [True, True, True, False, True],
        }
    )
    assert extract_vn30_tickers(listings) == ["ACB", "VCB"]


def test_dataframe_market_source_filters_loaded_frame():
    frame = pd.DataFrame(
        {
            "time": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
            "close": [100.0, 101.0, 102.0],
            "volume": [10, 11, 12],
        }
    )
    source = DataFrameMarketSource(frame)
    out = source.load_index_series(date(2024, 1, 3), date(2024, 1, 4))
    assert list(out["vn_index"]) == [101.0, 102.0]
    assert list(out.columns) == ["date", "vn_index", "volume"]
