from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from risk_dashboard.data.interfaces import MacroSource

REQUIRED_MACRO_COLS = (
    "period_end",
    "usd_vnd_rate",
    "usd_vnd_1m_change_pct",
    "sbv_interest_rate_pct",
)


def normalize_macro_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Chuẩn hoá bảng vĩ mô tháng."""
    missing = [c for c in REQUIRED_MACRO_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Thiếu cột vĩ mô bắt buộc {missing}. Cần: {REQUIRED_MACRO_COLS}")
    out = df.copy()
    out["period_end"] = pd.to_datetime(out["period_end"])
    for c in ("usd_vnd_rate", "usd_vnd_1m_change_pct", "sbv_interest_rate_pct"):
        out[c] = pd.to_numeric(out[c], errors="coerce")
    if "cpi_yoy_pct" in out.columns:
        out["cpi_yoy_pct"] = pd.to_numeric(out["cpi_yoy_pct"], errors="coerce")
    if "fdi_disbursement_yoy_pct" in out.columns:
        out["fdi_disbursement_yoy_pct"] = pd.to_numeric(out["fdi_disbursement_yoy_pct"], errors="coerce")
    if "liquidity_index" in out.columns:
        out["liquidity_index"] = pd.to_numeric(out["liquidity_index"], errors="coerce")
    out = out.dropna(subset=list(REQUIRED_MACRO_COLS)).sort_values("period_end").reset_index(drop=True)
    return out


class CsvMacroSource(MacroSource):
    """
    Đọc vĩ mô tháng từ CSV (tự nhập từ GSO/SBV hoặc nguồn thống kê).

    Cột bắt buộc: period_end (cuối tháng), usd_vnd_rate, usd_vnd_1m_change_pct, sbv_interest_rate_pct
    Tuỳ chọn: cpi_yoy_pct, fdi_disbursement_yoy_pct
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load_macro_monthly(self, start: date, end: date) -> pd.DataFrame:
        if start > end:
            raise ValueError("start must be <= end")
        raw = pd.read_csv(self.path)
        df = normalize_macro_monthly(raw)
        # merge_asof backward: giữ mọi mốc tháng có period_end <= end (kể cả trước ngày start daily).
        mask = df["period_end"] <= pd.Timestamp(end)
        return df.loc[mask].reset_index(drop=True)
