from datetime import date
from pathlib import Path

import pandas as pd

from risk_dashboard.data.macro_connector import CsvMacroSource, normalize_macro_monthly
from risk_dashboard.data.market_connector import CsvMarketSource, normalize_index_ohlcv_to_daily

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_normalize_index_ohlcv():
    raw = pd.read_csv(FIXTURES / "sample_market.csv")
    df = normalize_index_ohlcv_to_daily(raw)
    assert list(df.columns) == ["date", "vn_index", "volume"]
    assert len(df) == 4


def test_csv_market_source_range():
    src = CsvMarketSource(FIXTURES / "sample_market.csv")
    df = src.load_index_series(date(2024, 1, 1), date(2024, 1, 31))
    assert len(df) == 3


def test_macro_normalize_and_load():
    raw = pd.read_csv(FIXTURES / "sample_macro.csv")
    df = normalize_macro_monthly(raw)
    assert len(df) == 3
    src = CsvMacroSource(FIXTURES / "sample_macro.csv")
    m = src.load_macro_monthly(date(2024, 1, 1), date(2024, 12, 31))
    assert m["period_end"].max() <= pd.Timestamp("2024-12-31")
