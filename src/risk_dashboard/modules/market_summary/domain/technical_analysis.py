"""Pure Python technical analysis calculations for Market Summary."""

from __future__ import annotations

from typing import Literal
import pandas as pd
from risk_dashboard.modules.market_summary.domain.models import TechnicalOverview


def calculate_technical_overview(
    df_history: pd.DataFrame,
) -> TechnicalOverview | None:
    """Calculates short-term trend, support/resistance, and volume confirmation from index OHLCV history."""
    if df_history is None or len(df_history) < 20:
        return None

    df = df_history.copy().reset_index(drop=True)
    
    # Calculate SMA5 and SMA20
    df["sma5"] = df["close"].rolling(5).mean()
    df["sma20"] = df["close"].rolling(20).mean()
    df["sma20_vol"] = df["volume"].rolling(20).mean()

    latest = df.iloc[-1]
    prev_sma20 = df.iloc[-2]["sma20"] if len(df) >= 2 else latest["sma20"]

    # Trend logic
    close = float(latest["close"])
    sma5 = float(latest["sma5"])
    sma20 = float(latest["sma20"])
    sma20_slope = sma20 - prev_sma20

    if close > sma5 and sma5 > sma20 and sma20_slope >= 0:
        trend: Literal["BULLISH", "BEARISH", "NEUTRAL_SIDEWAYS"] = "BULLISH"
    elif close < sma5 and sma5 < sma20 and sma20_slope <= 0:
        trend = "BEARISH"
    else:
        trend = "NEUTRAL_SIDEWAYS"

    # Support & Resistance (rolling 20-session min/max)
    last_20 = df.iloc[-20:]
    low_20d = float(last_20["low"].min())
    high_20d = float(last_20["high"].max())

    supp_low = round(low_20d / 10.0) * 10
    supp_high = round((low_20d * 1.005) / 10.0) * 10
    rest_low = round((high_20d * 0.995) / 10.0) * 10
    rest_high = round(high_20d / 10.0) * 10

    support_zone = (min(supp_low, supp_high), max(supp_low, supp_high))
    resistance_zone = (min(rest_low, rest_high), max(rest_low, rest_high))

    # Volume confirmation
    cur_vol = float(latest["volume"])
    sma20_vol = float(latest["sma20_vol"])
    vol_ratio = (cur_vol / sma20_vol) if sma20_vol > 0 else 1.0

    if vol_ratio >= 1.2:
        vol_conf: Literal["HIGH", "NORMAL", "LOW"] = "HIGH"
    elif vol_ratio <= 0.8:
        vol_conf = "LOW"
    else:
        vol_conf = "NORMAL"

    # Neutral, objective technical commentary
    watch_points: list[str] = []

    # Support position analysis
    if close < support_zone[0]:
        watch_points.append(f"VN-Index đã đóng cửa phía dưới vùng hỗ trợ gần {support_zone[0]:.0f}–{support_zone[1]:.0f} điểm.")
    elif support_zone[0] <= close <= support_zone[1]:
        watch_points.append(f"VN-Index đang trong vùng kiểm định hỗ trợ {support_zone[0]:.0f}–{support_zone[1]:.0f} điểm.")
    else:
        watch_points.append(f"VN-Index tiếp tục duy trì trên vùng hỗ trợ gần {support_zone[0]:.0f}–{support_zone[1]:.0f} điểm.")

    # Resistance position analysis
    if close > resistance_zone[1]:
        if vol_conf == "HIGH":
            watch_points.append(f"VN-Index đóng cửa phía trên vùng kháng cự {resistance_zone[0]:.0f}–{resistance_zone[1]:.0f} điểm, kèm thanh khoản cao hơn trung bình 20 phiên.")
        else:
            watch_points.append(f"VN-Index đóng cửa phía trên vùng kháng cự gần {resistance_zone[0]:.0f}–{resistance_zone[1]:.0f} điểm.")
    elif resistance_zone[0] <= close <= resistance_zone[1]:
        watch_points.append(f"VN-Index đang giao dịch và kiểm định trực tiếp vùng kháng cự {resistance_zone[0]:.0f}–{resistance_zone[1]:.0f} điểm.")
    else:
        watch_points.append(f"Vùng kháng cự ngắn hạn tiếp theo dự kiến tại {resistance_zone[0]:.0f}–{resistance_zone[1]:.0f} điểm.")

    return TechnicalOverview(
        short_term_trend=trend,
        support_zone=support_zone,
        resistance_zone=resistance_zone,
        volume_confirmation=vol_conf,
        watch_points=watch_points,
    )
