from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from risk_dashboard.data import watchlist_prices as watchlist_prices_mod

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Watchlist"])


class WatchlistSyncBody(BaseModel):
    tickers: list[str] = Field(..., min_length=1, max_length=40)


@router.post("/watchlist/prices/sync", tags=["Watchlist"])
def watchlist_prices_sync(body: WatchlistSyncBody):
    try:
        return watchlist_prices_mod.sync_watchlist_tickers(body.tickers)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/watchlist/prices/{ticker}", tags=["Watchlist"])
def watchlist_prices_get(ticker: str):
    try:
        t = watchlist_prices_mod.parse_ticker_list([ticker])[0]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        df = watchlist_prices_mod.sync_watchlist_ticker(t)
    except Exception as exc:
        logger.exception("watchlist OHLCV %s", t)
        raise HTTPException(status_code=503, detail=f"Không lấy được dữ liệu giá: {exc}") from exc

    return {
        "ticker": t,
        "rows": len(df),
        "from": str(df.index.min().date()) if len(df) else None,
        "to": str(df.index.max().date()) if len(df) else None,
        "source": "yfinance + cache (data/watchlist_prices)",
        "bars": watchlist_prices_mod.ohlcv_to_bars_json(df),
    }
