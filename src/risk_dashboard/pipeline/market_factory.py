from __future__ import annotations

from typing import Literal

from risk_dashboard.data.interfaces import MarketSource
from risk_dashboard.data.market_connector import (
    CsvMarketSource,
    VnstockMarketSource,
    YfinanceMarketSource,
)

MarketMode = Literal["vnstock", "yfinance", "csv"]


def create_market_source(
    mode: MarketMode,
    *,
    csv_path: str | None = None,
    vnindex_symbol: str = "VNINDEX",
    vnstock_source: str = "VCI",
    yfinance_ticker: str | None = None,
) -> MarketSource:
    """
    Factory nguồn thị trường — tách riêng để đổi backend (vnstock / yfinance / CSV) không đụng macro.
    """
    if mode == "csv":
        if not csv_path:
            raise ValueError("mode=csv cần csv_path")
        return CsvMarketSource(csv_path)
    if mode == "vnstock":
        return VnstockMarketSource(symbol=vnindex_symbol, source=vnstock_source)
    if mode == "yfinance":
        if not yfinance_ticker:
            raise ValueError("mode=yfinance cần yfinance_ticker")
        return YfinanceMarketSource(yfinance_ticker)
    raise ValueError(f"Unknown market mode: {mode}")


def market_label(mode: MarketMode, **kw: str) -> str:
    if mode == "csv":
        return f"csv:{kw.get('csv_path', '')}"
    if mode == "vnstock":
        return f"vnstock:{kw.get('vnindex_symbol', 'VNINDEX')}:{kw.get('vnstock_source', 'VCI')}"
    if mode == "yfinance":
        return f"yfinance:{kw.get('yfinance_ticker', '')}"
    return str(mode)
