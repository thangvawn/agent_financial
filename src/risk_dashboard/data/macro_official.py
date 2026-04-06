from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pandas as pd

from risk_dashboard.data.interfaces import MacroSource
from risk_dashboard.data.macro_connector import normalize_macro_monthly


def _strip_cols(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    return out


def _map_known_headers(df: pd.DataFrame) -> pd.DataFrame:
    mapping: dict[str, str] = {}
    for c in df.columns:
        key = re.sub(r"\s+", "_", str(c).strip().lower())
        if key in ("period_end", "cuoi_thang", "ngay", "date", "thoi_diem"):
            mapping[c] = "period_end"
        elif key in ("usd_vnd_rate", "ty_gia_usd", "usd/vnd", "usd_vnd", "tg_usd"):
            mapping[c] = "usd_vnd_rate"
        elif key in ("usd_vnd_1m_change_pct", "bien_dong_tg_1m", "thay_doi_tg_1m", "tg_1m_pct"):
            mapping[c] = "usd_vnd_1m_change_pct"
        elif key in ("sbv_interest_rate_pct", "lai_suat", "lai_suat_dieu_hanh", "ls_dieu_hanh", "policy_rate"):
            mapping[c] = "sbv_interest_rate_pct"
        elif key in ("cpi_yoy_pct", "cpi_yoy", "lam_phat", "toc_do_tang_cpi"):
            mapping[c] = "cpi_yoy_pct"
        elif key in ("fdi_disbursement_yoy_pct", "fdi_yoy", "giai_ngan_fdi_yoy"):
            mapping[c] = "fdi_disbursement_yoy_pct"
        elif key in ("liquidity_index", "thanh_khoan", "liquidity_stress"):
            mapping[c] = "liquidity_index"
    if not mapping:
        return df
    out = df.rename(columns=mapping)
    dup = out.columns[out.columns.duplicated()].tolist()
    if dup:
        out = out.loc[:, ~out.columns.duplicated()].copy()
    return out


def _coerce_period_end(series: pd.Series) -> pd.Series:
    dt = pd.to_datetime(series, errors="coerce", dayfirst=False)
    if dt.notna().sum() >= max(1, len(series) // 2):
        return dt
    dt = pd.to_datetime(series, errors="coerce", dayfirst=True)
    if dt.notna().sum() >= max(1, len(series) // 2):
        return dt
    as_str = series.astype(str).str.strip()
    dt2 = pd.to_datetime(as_str + "-01", format="%Y-%m-%d", errors="coerce")
    if dt2.notna().any():
        return dt2 + pd.offsets.MonthEnd(0)
    return dt


def read_official_macro_csv(path: str | Path) -> pd.DataFrame:
    """
    Đọc CSV (tên cột linh hoạt, có thể xuất từ GSO/SBV) → chuẩn `normalize_macro_monthly`.
    """
    raw = pd.read_csv(path)
    df = _strip_cols(raw)
    df = _map_known_headers(df)
    if "period_end" not in df.columns:
        raise ValueError(
            "Không nhận diện được cột ngày/tháng. Dùng 'period_end' hoặc 'cuoi_thang' / 'ngay'."
        )
    df["period_end"] = _coerce_period_end(df["period_end"])
    return normalize_macro_monthly(df)


class OfficialCsvMacroSource(MacroSource):
    """Giống CsvMacroSource nhưng đọc qua `read_official_macro_csv` (alias cột tiếng Việt)."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load_macro_monthly(self, start: date, end: date) -> pd.DataFrame:
        if start > end:
            raise ValueError("start must be <= end")
        df = read_official_macro_csv(self.path)
        mask = df["period_end"] <= pd.Timestamp(end)
        return df.loc[mask].reset_index(drop=True)
