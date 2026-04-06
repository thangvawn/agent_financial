from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd


REQUIRED_SECTOR_COLS = ("month_end", "sector_code", "return_pct")


def normalize_sector_monthly(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in REQUIRED_SECTOR_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Thiếu cột sector: {missing}. Cần: {REQUIRED_SECTOR_COLS}")
    out = df.copy()
    out["month_end"] = pd.to_datetime(out["month_end"])
    out["return_pct"] = pd.to_numeric(out["return_pct"], errors="coerce")
    out["sector_code"] = out["sector_code"].astype(str).str.strip()
    return out.dropna(subset=list(REQUIRED_SECTOR_COLS)).sort_values(["month_end", "sector_code"]).reset_index(drop=True)


def load_sector_panel_csv(path: str | Path) -> pd.DataFrame:
    """CSV: month_end, sector_code, return_pct (hoặc lợi nhuận ngành so với tháng trước)."""
    return normalize_sector_monthly(pd.read_csv(path))


@dataclass
class SectorWinnersLosers:
    winners: list[tuple[str, float]]
    losers: list[tuple[str, float]]
    window_months: int


def sector_winners_losers(
    panel: pd.DataFrame,
    as_of: date,
    *,
    window_months: int = 6,
    top_k: int = 5,
) -> SectorWinnersLosers:
    """
    Từ bảng lịch sử ngành (tháng), tính tổng lợi (%) trong cửa sổ gần nhất và xếp hạng.
    """
    df = panel.copy()
    df["month_end"] = pd.to_datetime(df["month_end"])
    end = pd.Timestamp(as_of)
    start = end - pd.DateOffset(months=window_months + 1)
    sub = df[(df["month_end"] > start) & (df["month_end"] <= end)]
    if sub.empty:
        return SectorWinnersLosers(winners=[], losers=[], window_months=window_months)
    agg = sub.groupby("sector_code", as_index=False)["return_pct"].sum()
    agg = agg.sort_values("return_pct", ascending=False)
    winners = [
        (str(r["sector_code"]), float(r["return_pct"]))
        for _, r in agg.head(top_k).iterrows()
    ]
    losers = [
        (str(r["sector_code"]), float(r["return_pct"]))
        for _, r in agg.tail(top_k).iloc[::-1].iterrows()
    ]
    return SectorWinnersLosers(winners=winners, losers=losers, window_months=window_months)