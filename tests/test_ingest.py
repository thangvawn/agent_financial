from datetime import date
from pathlib import Path

import pandas as pd

from risk_dashboard.data.ingest import build_training_panel, run_ingest_to_parquet
from risk_dashboard.data.macro_connector import CsvMacroSource
from risk_dashboard.data.market_connector import CsvMarketSource

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_build_training_panel():
    market = CsvMarketSource(FIXTURES / "sample_market.csv")
    macro = CsvMacroSource(FIXTURES / "sample_macro.csv")
    panel = build_training_panel(market, macro, date(2024, 1, 1), date(2024, 2, 29))
    assert "usd_vnd_rate" in panel.columns
    assert "volume_1w_trend_pct" in panel.columns
    assert len(panel) >= 1


def test_run_ingest_to_parquet(tmp_path):
    market = CsvMarketSource(FIXTURES / "sample_market.csv")
    macro = CsvMacroSource(FIXTURES / "sample_macro.csv")
    pq, mj = run_ingest_to_parquet(
        market,
        macro,
        date(2024, 1, 1),
        date(2024, 2, 29),
        tmp_path,
        market_label="test",
        macro_label="test",
    )
    assert pq.exists()
    assert mj.exists()
    df = pd.read_parquet(pq)
    assert not df.empty
