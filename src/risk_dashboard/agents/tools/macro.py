"""
Macro Tool — Kết nối trực tiếp vào yfinance + World Bank API.
Không dùng mock data, không if-else.
"""
from __future__ import annotations

from datetime import date, timedelta

from langchain_core.tools import tool


@tool
def get_macro_indicators(indicator: str) -> dict:
    """Lấy dữ liệu vĩ mô THẬT từ API. 
    indicator: 'fx' (tỷ giá USD/VND), 'interest_rate' (lãi suất), 'cpi' (lạm phát).
    Trả về dict chứa giá trị mới nhất, xu hướng, và chuỗi lịch sử gần nhất."""
    
    ind = indicator.lower().strip()
    today = date.today()
    
    if ind in ("fx", "tỷ giá", "usd", "exchange"):
        return _fetch_fx_live()
    elif ind in ("interest_rate", "lãi suất", "rate"):
        return _fetch_interest_rate()
    elif ind in ("cpi", "lạm phát", "inflation"):
        return _fetch_cpi()
    else:
        # Fallback: thử lấy tỷ giá — indicator phổ biến nhất
        return _fetch_fx_live()


def _fetch_fx_live() -> dict:
    """Kéo tỷ giá USD/VND thật từ yfinance."""
    try:
        import yfinance as yf
        t = yf.Ticker("USDVND=X")
        hist = t.history(period="5d", auto_adjust=True)
        if hist is None or hist.empty:
            return {"error": "yfinance không trả dữ liệu tỷ giá."}
        
        close = hist["Close"].dropna()
        latest = float(close.iloc[-1])
        prev = float(close.iloc[-2]) if len(close) >= 2 else latest
        change_pct = round((latest - prev) / prev * 100, 3)
        
        return {
            "indicator": "USD/VND Exchange Rate",
            "latest_value": round(latest, 2),
            "previous_value": round(prev, 2),
            "daily_change_pct": change_pct,
            "trend": "tăng" if change_pct > 0.05 else ("giảm" if change_pct < -0.05 else "đi ngang"),
            "source": "Yahoo Finance (USDVND=X)",
            "as_of": str(close.index[-1].date()),
        }
    except Exception as e:
        return {"error": f"Không thể lấy tỷ giá: {e}"}


def _fetch_interest_rate() -> dict:
    """Kéo lãi suất từ World Bank API."""
    try:
        from risk_dashboard.data.macro_auto import _wb_fetch_indicator, WB_LENDING_RATE
        import pandas as pd
        
        end_year = date.today().year
        df = _wb_fetch_indicator(WB_LENDING_RATE, end_year - 3, end_year)
        if df.empty:
            return {"error": "World Bank không trả dữ liệu lãi suất."}
        
        latest = df.iloc[-1]
        return {
            "indicator": "Vietnam Lending Rate",
            "latest_value_pct": round(float(latest["value"]), 2),
            "year": int(latest["year"]),
            "history": df.tail(5).to_dict(orient="records"),
            "source": "World Bank (FR.INR.LEND)",
        }
    except Exception as e:
        return {"error": f"Không thể lấy lãi suất: {e}"}


def _fetch_cpi() -> dict:
    """Kéo CPI từ World Bank API."""
    try:
        from risk_dashboard.data.macro_auto import _wb_fetch_indicator, WB_INFLATION_YOY
        
        end_year = date.today().year
        df = _wb_fetch_indicator(WB_INFLATION_YOY, end_year - 3, end_year)
        if df.empty:
            return {"error": "World Bank không trả dữ liệu CPI."}
        
        latest = df.iloc[-1]
        return {
            "indicator": "Vietnam CPI YoY",
            "latest_value_pct": round(float(latest["value"]), 2),
            "year": int(latest["year"]),
            "history": df.tail(5).to_dict(orient="records"),
            "source": "World Bank (FP.CPI.TOTL.ZG)",
        }
    except Exception as e:
        return {"error": f"Không thể lấy CPI: {e}"}
