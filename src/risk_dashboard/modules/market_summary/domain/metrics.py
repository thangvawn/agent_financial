"""Pure Python metrics calculations for Market Summary."""

from __future__ import annotations

import pandas as pd
from risk_dashboard.modules.market_summary.domain.models import (
    CapitalFlow,
    IndexMetrics,
    MarketBreadth,
    StockContribution,
)


def calculate_index_metrics(
    symbol: str,
    df_history: pd.DataFrame,
) -> IndexMetrics | None:
    """Calculates index points, percentage changes, and comparisons vs previous session and 20-session SMA."""
    if df_history is None or df_history.empty:
        return None

    df = df_history.copy().reset_index(drop=True)
    if len(df) < 2:
        latest = df.iloc[-1]
        close = float(latest["close"])
        return IndexMetrics(
            symbol=symbol,
            close=close,
            change_points=0.0,
            change_pct=0.0,
            volume=int(latest.get("volume", 0)),
            value_vnd=float(latest.get("value", 0.0)),
        )

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    close = float(latest["close"])
    prev_close = float(prev["close"])
    change_points = close - prev_close
    change_pct = (change_points / prev_close) * 100.0 if prev_close > 0 else 0.0

    volume = int(latest.get("volume", 0))
    prev_vol = int(prev.get("volume", 0))
    vol_vs_prev_pct = ((volume - prev_vol) / prev_vol * 100.0) if prev_vol > 0 else 0.0

    value_vnd = float(latest.get("value", 0.0))
    prev_val = float(prev.get("value", 0.0))
    value_vs_prev_pct = ((value_vnd - prev_val) / prev_val * 100.0) if prev_val > 0 else 0.0

    vol_vs_sma20_pct: float | None = None
    value_vs_sma20_pct: float | None = None

    if len(df) >= 20:
        last_20 = df.iloc[-20:]
        sma20_vol = last_20["volume"].mean()
        sma20_val = last_20["value"].mean() if "value" in last_20.columns else 0.0

        if sma20_vol > 0:
            vol_vs_sma20_pct = float((volume - sma20_vol) / sma20_vol * 100.0)
        if sma20_val > 0:
            value_vs_sma20_pct = float((value_vnd - sma20_val) / sma20_val * 100.0)

    return IndexMetrics(
        symbol=symbol,
        close=round(close, 2),
        change_points=round(change_points, 2),
        change_pct=round(change_pct, 2),
        volume=volume,
        value_vnd=value_vnd,
        vol_vs_prev_pct=round(vol_vs_prev_pct, 2) if vol_vs_prev_pct is not None else None,
        vol_vs_sma20_pct=round(vol_vs_sma20_pct, 2) if vol_vs_sma20_pct is not None else None,
        value_vs_prev_pct=round(value_vs_prev_pct, 2) if value_vs_prev_pct is not None else None,
        value_vs_sma20_pct=round(value_vs_sma20_pct, 2) if value_vs_sma20_pct is not None else None,
    )


def calculate_market_breadth(
    advancers: int,
    decliners: int,
    unchanged: int,
    ceiling: int = 0,
    floor: int = 0,
) -> MarketBreadth:
    """Classifies market breadth and provides qualitative assessment."""
    total = advancers + decliners + unchanged
    if total == 0:
        assessment = "Chưa có dữ liệu độ rộng"
    else:
        ratio = advancers / decliners if decliners > 0 else (advancers if advancers > 0 else 1.0)
        if advancers > decliners * 1.5:
            assessment = "Dòng tiền lan tỏa tích cực trên diện rộng."
        elif decliners > advancers * 1.5:
            assessment = "Áp lực điều chỉnh áp đảo trên diện rộng."
        elif ratio >= 1.0:
            assessment = "Độ rộng nghiêng nhẹ về bên mua, dòng tiền phân hóa."
        else:
            assessment = "Độ rộng nghiêng nhẹ về bên bán, áp lực chốt lời gia tăng."

    return MarketBreadth(
        advancers=advancers,
        decliners=decliners,
        unchanged=unchanged,
        ceiling=ceiling,
        floor=floor,
        summary_assessment=assessment,
    )


def calculate_capital_flow(
    foreign_df: pd.DataFrame | None,
    sector_df: pd.DataFrame | None = None,
) -> CapitalFlow:
    """Calculates net foreign trading values (in Billion VND) and sector movements."""
    if foreign_df is None or foreign_df.empty:
        return CapitalFlow(is_available=False)

    df = foreign_df.copy()
    # Expect columns: symbol, net_value (or buy_value, sell_value)
    if "net_value" not in df.columns:
        if "buy_value" in df.columns and "sell_value" in df.columns:
            df["net_value"] = df["buy_value"] - df["sell_value"]
        else:
            return CapitalFlow(is_available=False)

    total_net_vnd = df["net_value"].sum()
    total_net_billion = round(float(total_net_vnd) / 1e9, 2)

    df_sorted = df.sort_values(by="net_value", ascending=False)
    top_buy_df = df_sorted[df_sorted["net_value"] > 0].head(5)
    top_sell_df = df_sorted[df_sorted["net_value"] < 0].tail(5).sort_values(by="net_value", ascending=True)

    top_buy = [
        (str(row["symbol"]), round(float(row["net_value"]) / 1e9, 2))
        for _, row in top_buy_df.iterrows()
    ]
    top_sell = [
        (str(row["symbol"]), round(abs(float(row["net_value"])) / 1e9, 2))
        for _, row in top_sell_df.iterrows()
    ]

    leading_sectors: list[str] = []
    weakening_sectors: list[str] = []
    if sector_df is not None and not sector_df.empty:
        if "sector" in sector_df.columns and "change_pct" in sector_df.columns:
            sec_sorted = sector_df.sort_values(by="change_pct", ascending=False)
            leading_sectors = sec_sorted.head(3)["sector"].tolist()
            weakening_sectors = sec_sorted.tail(3).sort_values(by="change_pct", ascending=True)["sector"].tolist()

    return CapitalFlow(
        is_available=True,
        leading_sectors=leading_sectors,
        weakening_sectors=weakening_sectors,
        net_foreign_val_billion=total_net_billion,
        top_foreign_buy=top_buy,
        top_foreign_sell=top_sell,
    )
