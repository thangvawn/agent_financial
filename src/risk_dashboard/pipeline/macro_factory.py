from __future__ import annotations

from typing import Literal

from risk_dashboard.data.interfaces import MacroSource
from risk_dashboard.data.macro_auto import AutoMacroSource
from risk_dashboard.data.macro_connector import CsvMacroSource
from risk_dashboard.data.macro_official import OfficialCsvMacroSource

MacroMode = Literal["auto", "csv", "official"]


def create_macro_source(
    mode: MacroMode,
    *,
    macro_csv_path: str | None = None,
    yfinance_fx_ticker: str = "USDVND=X",
) -> MacroSource:
    """
    Factory vĩ mô — tách khỏi market để thay World Bank / CSV / GSO-style độc lập.
    """
    if mode == "auto":
        return AutoMacroSource(yfinance_ticker=yfinance_fx_ticker)
    if mode == "csv":
        if not macro_csv_path:
            raise ValueError("mode=csv cần macro_csv_path")
        return CsvMacroSource(macro_csv_path)
    if mode == "official":
        if not macro_csv_path:
            raise ValueError("mode=official cần macro_csv_path (file alias tiếng Việt)")
        return OfficialCsvMacroSource(macro_csv_path)
    raise ValueError(f"Unknown macro mode: {mode}")


def macro_label(mode: str, **kw: str) -> str:
    if mode == "auto":
        return f"auto:yfinance:{kw.get('yfinance_fx_ticker', 'USDVND=X')}+worldbank"
    if mode == "csv":
        return f"csv:{kw.get('macro_csv_path', '')}"
    if mode == "official":
        return f"official:{kw.get('macro_csv_path', '')}"
    return mode
