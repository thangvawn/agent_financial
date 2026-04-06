from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from risk_dashboard.schemas.snapshots import DailyFeatureRow, MacroFeatures, MarketFeatures


def _ensure_datetime(df: pd.DataFrame, col: str) -> pd.DataFrame:
    out = df.copy()
    out[col] = pd.to_datetime(out[col])
    return out.sort_values(col).reset_index(drop=True)


def align_mixed_frequency(
    daily: pd.DataFrame,
    monthly: pd.DataFrame,
    *,
    daily_date_col: str = "date",
    monthly_date_col: str = "period_end",
) -> pd.DataFrame:
    """
    Gộp dữ liệu ngày với bảng tháng bằng merge_asof (backward):
    mỗi ngày nhận bản ghi tháng mới nhất đã biết tại thời điểm đó.
    """
    d = _ensure_datetime(daily, daily_date_col)
    m = _ensure_datetime(monthly, monthly_date_col).rename(columns={monthly_date_col: "_macro_date"})
    macro_cols = [c for c in m.columns if c != "_macro_date"]
    merged = pd.merge_asof(
        d,
        m,
        left_on=daily_date_col,
        right_on="_macro_date",
        direction="backward",
    )
    merged = merged.drop(columns=["_macro_date"], errors="ignore")
    for c in macro_cols:
        merged[c] = merged[c].ffill()
    return merged


def weekly_volume_trend_pct(volume_series: pd.Series, *, window: int = 5) -> float:
    """So sánh trung bình volume 5 phiên gần nhất với 5 phiên trước đó (%)."""
    if len(volume_series) < window * 2:
        return 0.0
    recent = volume_series.iloc[-window:].mean()
    prev = volume_series.iloc[-window * 2 : -window].mean()
    if prev == 0:
        return 0.0
    return float((recent - prev) / abs(prev) * 100.0)


def build_daily_feature_row(
    as_of: date,
    aligned_row: pd.Series,
    *,
    date_col: str = "date",
    vn_index_col: str = "vn_index",
    volume_col: str = "volume",
    usd_col: str = "usd_vnd_rate",
    usd_1m_col: str = "usd_vnd_1m_change_pct",
    sbv_col: str = "sbv_interest_rate_pct",
    cpi_col: str | None = "cpi_yoy_pct",
    fdi_col: str | None = "fdi_disbursement_yoy_pct",
) -> DailyFeatureRow:
    macro = MacroFeatures(
        usd_vnd_rate=float(aligned_row[usd_col]),
        usd_vnd_1m_change_pct=float(aligned_row[usd_1m_col]),
        sbv_interest_rate_pct=float(aligned_row[sbv_col]),
        cpi_yoy_pct=float(aligned_row[cpi_col]) if cpi_col and cpi_col in aligned_row and pd.notna(aligned_row.get(cpi_col)) else None,
        fdi_disbursement_yoy_pct=float(aligned_row[fdi_col])
        if fdi_col and fdi_col in aligned_row and pd.notna(aligned_row.get(fdi_col))
        else None,
    )
    market = MarketFeatures(
        vn_index=float(aligned_row[vn_index_col]),
        volume_1w_trend_pct=float(aligned_row.get("volume_1w_trend_pct", 0.0)),
    )
    d = aligned_row[date_col]
    if hasattr(d, "date"):
        d = d.date()
    return DailyFeatureRow(date=d if isinstance(d, date) else pd.Timestamp(d).date(), market=market, macro=macro)


def slice_trading_window(daily: pd.DataFrame, as_of: date, *, days: int, date_col: str = "date") -> pd.DataFrame:
    dd = _ensure_datetime(daily, date_col)
    end = pd.Timestamp(as_of)
    start = end - timedelta(days=days)
    mask = (dd[date_col] >= start) & (dd[date_col] <= end)
    return dd.loc[mask].reset_index(drop=True)
