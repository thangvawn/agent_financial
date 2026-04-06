from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import date
from typing import Any

import pandas as pd

from risk_dashboard.data.interfaces import MacroSource
from risk_dashboard.data.macro_connector import normalize_macro_monthly

WB_COUNTRY = "VN"
WB_INFLATION_YOY = "FP.CPI.TOTL.ZG"
WB_LENDING_RATE = "FR.INR.LEND"
# FDI ròng (current US$) — YoY % tính trên chuỗi năm, gán xuống tháng
WB_FDI_INFLOW_USD = "BX.KLT.DINV.CD.WD"


def _wb_fetch_indicator(indicator: str, start_year: int, end_year: int) -> pd.DataFrame:
    url = (
        f"https://api.worldbank.org/v2/country/{WB_COUNTRY}/indicator/{indicator}"
        f"?date={start_year}:{end_year}&format=json&per_page=500"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "risk-dashboard/0.1"})
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
            break
        except (TimeoutError, urllib.error.URLError, OSError) as e:
            last_err = e
            time.sleep(2.0 * (attempt + 1))
    else:
        raise RuntimeError(f"World Bank API timeout/lỗi mạng sau 3 lần: {last_err}") from last_err
    if not isinstance(raw, list) or len(raw) < 2:
        raise ValueError(f"World Bank response không hợp lệ: {indicator}")
    rows = raw[1]
    if not rows:
        return pd.DataFrame(columns=["year", "value"])
    rec: list[dict[str, Any]] = []
    for r in rows:
        if r.get("value") is None:
            continue
        rec.append({"year": int(r["date"]), "value": float(r["value"])})
    return pd.DataFrame(rec).sort_values("year").reset_index(drop=True)


def _annual_value_for_year(df: pd.DataFrame, year: int) -> float:
    """Lấy giá trị năm `year`, hoặc năm gần nhất có dữ liệu."""
    if df.empty:
        return float("nan")
    sub = df[df["year"] == year]
    if not sub.empty:
        return float(sub["value"].iloc[-1])
    before = df[df["year"] <= year]
    if not before.empty:
        return float(before["value"].iloc[-1])
    return float(df["value"].iloc[0])


def _map_annual_to_month_ends(df_year: pd.DataFrame, month_ends: pd.DatetimeIndex) -> pd.Series:
    vals = []
    for ts in month_ends:
        vals.append(_annual_value_for_year(df_year, ts.year))
    return pd.Series(vals, index=month_ends)


def _fetch_usd_vnd_monthly_yfinance(ticker: str, start: date, end: date) -> pd.DataFrame:
    try:
        import yfinance as yf  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            'Cần cài yfinance: pip install "yfinance>=0.2" hoặc pip install -e ".[auto]"'
        ) from e

    # Dùng Ticker.history tránh lỗi parse ngày với yfinance.download (USDVND=X, v.v.)
    t = yf.Ticker(ticker)
    ts_start = pd.Timestamp(start).normalize()
    ts_end = pd.Timestamp(end).normalize() + pd.Timedelta(days=1)
    df = t.history(start=ts_start, end=ts_end, auto_adjust=True, interval="1d")
    if df is None or df.empty:
        raise RuntimeError(f"yfinance không trả dữ liệu cho {ticker} trong khoảng đã chọn.")
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    col = "Close" if "Close" in df.columns else "Adj Close"
    close = df[col].squeeze()
    if hasattr(close.index, "tz") and close.index.tz is not None:
        close.index = close.index.tz_localize(None)
    monthly = close.resample("ME").last().dropna()
    monthly = monthly.loc[(monthly.index >= pd.Timestamp(start)) & (monthly.index <= pd.Timestamp(end))]
    if monthly.empty:
        raise RuntimeError("Không đủ điểm tỷ giá sau khi gom tháng.")
    rates = monthly.astype(float)
    mom_pct = rates.pct_change() * 100.0
    return pd.DataFrame(
        {
            "period_end": rates.index.normalize(),
            "usd_vnd_rate": rates.values,
            "usd_vnd_1m_change_pct": mom_pct.fillna(0.0).values,
        }
    )


class AutoMacroSource(MacroSource):
    """
    Vĩ mô tự động (ước lượng cho pipeline):

    - **usd_vnd_rate**, **usd_vnd_1m_change_pct**: Yahoo Finance (`yfinance`), mặc định `USDVND=X`.
    - **cpi_yoy_pct**: World Bank — lạm phát CPI năm (`FP.CPI.TOTL.ZG`), gán đồng nhất các tháng trong năm.
    - **sbv_interest_rate_pct**: World Bank — lãi cho vay (`FR.INR.LEND`), cùng cách gán.

    Lưu ý: CPI/lãi từ WB là **chuỗi năm** → biến tháng là **xấp xỉ**, không thay số SBV/GSO chính thức.
    """

    def __init__(self, *, yfinance_ticker: str = "USDVND=X") -> None:
        self.yfinance_ticker = yfinance_ticker

    def load_macro_monthly(self, start: date, end: date) -> pd.DataFrame:
        if start > end:
            raise ValueError("start must be <= end")
        start_year = start.year - 1
        end_year = end.year + 1

        fx = _fetch_usd_vnd_monthly_yfinance(self.yfinance_ticker, start, end)
        month_idx = pd.DatetimeIndex(pd.to_datetime(fx["period_end"]))

        inf_df = _wb_fetch_indicator(WB_INFLATION_YOY, start_year, end_year)
        lend_df = _wb_fetch_indicator(WB_LENDING_RATE, start_year, end_year)
        fdi_df = _wb_fetch_indicator(WB_FDI_INFLOW_USD, start_year, end_year)
        if not fdi_df.empty:
            fdi_df = fdi_df.sort_values("year").reset_index(drop=True)
            fdi_df["fdi_yoy_pct"] = fdi_df["value"].pct_change() * 100.0
            fdi_yoy_annual = fdi_df[["year", "fdi_yoy_pct"]].rename(columns={"fdi_yoy_pct": "value"})
        else:
            fdi_yoy_annual = pd.DataFrame(columns=["year", "value"])

        cpi_series = _map_annual_to_month_ends(inf_df, month_idx)
        lend_series = _map_annual_to_month_ends(lend_df, month_idx)
        fdi_series = _map_annual_to_month_ends(fdi_yoy_annual, month_idx) if not fdi_yoy_annual.empty else None

        merged = fx.copy()
        merged["cpi_yoy_pct"] = cpi_series.values
        merged["sbv_interest_rate_pct"] = lend_series.values
        if fdi_series is not None:
            merged["fdi_disbursement_yoy_pct"] = fdi_series.values
        merged["period_end"] = pd.to_datetime(merged["period_end"])

        merged["cpi_yoy_pct"] = pd.to_numeric(merged["cpi_yoy_pct"], errors="coerce")
        merged["sbv_interest_rate_pct"] = pd.to_numeric(merged["sbv_interest_rate_pct"], errors="coerce")

        if merged["sbv_interest_rate_pct"].notna().sum() == 0:
            raise RuntimeError(
                "Không có dữ liệu lãi cho vay (World Bank) — thử mở rộng khoảng ngày hoặc dùng --macro-csv."
            )

        merged["sbv_interest_rate_pct"] = merged["sbv_interest_rate_pct"].ffill().bfill()
        merged["cpi_yoy_pct"] = merged["cpi_yoy_pct"].ffill().bfill()

        if merged["sbv_interest_rate_pct"].isna().any():
            merged["sbv_interest_rate_pct"] = merged["sbv_interest_rate_pct"].fillna(
                merged["sbv_interest_rate_pct"].median()
            )

        if merged["cpi_yoy_pct"].isna().any():
            merged["cpi_yoy_pct"] = merged["cpi_yoy_pct"].fillna(merged["cpi_yoy_pct"].median())

        if "fdi_disbursement_yoy_pct" in merged.columns:
            merged["fdi_disbursement_yoy_pct"] = merged["fdi_disbursement_yoy_pct"].ffill().bfill()

        out = normalize_macro_monthly(merged)
        mask = out["period_end"] <= pd.Timestamp(end)
        return out.loc[mask].reset_index(drop=True)
