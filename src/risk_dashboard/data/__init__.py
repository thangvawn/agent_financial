"""
Data layer: connectors, ETL, và ingest pipeline.

- ``interfaces``: abstract base classes (MacroSource, MarketSource)
- ``market_connector``: nguồn giá OHLCV (CSV, vnstock)
- ``macro_connector / macro_auto / macro_official``: nguồn vĩ mô
- ``sector_connector``: dữ liệu ngành
- ``financials``: tải BCTC (balance sheet, P&L, cash flow)
- ``etl``: align tần suất, build daily feature row
- ``ingest``: orchestrate full training panel
- ``universe_fetch``: fetch VN30, VNINDEX universe
- ``cross_asset_prices``: gold, USD, DXY...
- ``watchlist_prices``: OHLCV watchlist cache
- ``google_drive``: upload/download file học liệu
"""
from risk_dashboard.data.etl import align_mixed_frequency, build_daily_feature_row
from risk_dashboard.data.ingest import build_training_panel, run_ingest_to_parquet
from risk_dashboard.data.interfaces import MacroSource, MarketSource
from risk_dashboard.data.macro_auto import AutoMacroSource
from risk_dashboard.data.macro_connector import CsvMacroSource
from risk_dashboard.data.macro_official import OfficialCsvMacroSource, read_official_macro_csv
from risk_dashboard.data.market_connector import CsvMarketSource, VnstockMarketSource
from risk_dashboard.data.sector_connector import load_sector_panel_csv, sector_winners_losers
from risk_dashboard.data.universe_fetch import extract_vn30_tickers, fetch_market_universe_bundle

__all__ = [
    "MacroSource",
    "MarketSource",
    "AutoMacroSource",
    "CsvMacroSource",
    "OfficialCsvMacroSource",
    "read_official_macro_csv",
    "CsvMarketSource",
    "VnstockMarketSource",
    "extract_vn30_tickers",
    "fetch_market_universe_bundle",
    "load_sector_panel_csv",
    "sector_winners_losers",
    "align_mixed_frequency",
    "build_daily_feature_row",
    "build_training_panel",
    "run_ingest_to_parquet",
]
