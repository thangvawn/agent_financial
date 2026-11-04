"""One registry for conditions, UI explanations and ranking directions."""

from __future__ import annotations

from .indicators import average, number

VERSION = "vn-eod-1.0.0"
# label, group, score features; missing components never get redistributed weights.
PRESETS = {
    "breakout": ("Breakout có xác nhận", "bullish", ("rs63_pct", "log_rvol_pct", "clv_pct")),
    "strong_trend": ("Xu hướng tăng bền", "bullish", ("momentum_score", "slope50_pct")),
    "money_inflow": ("Áp lực mua", "bullish", ("cmf20_pct", "log_rvol_pct", "clv_pct")),
    "bottom_fishing": ("Hồi phục từ quá bán", "experimental", ("rsi_change_pct", "log_rvol_pct")),
    "vcp_pattern": (
        "Nền giá co hẹp",
        "experimental",
        ("neg_contraction_pct", "neg_bb_width_pct", "neg_volume_contraction_pct"),
    ),
    "overbought_peak": ("Giá tăng quá xa nền", "bearish", ("extension_pct", "rsi14_pct")),
    "bearish_reversal": (
        "Suy yếu xu hướng",
        "bearish",
        ("below_ma_atr_pct", "log_rvol_pct", "neg_clv_pct"),
    ),
    "dumping_signal": (
        "Áp lực bán bất thường",
        "bearish",
        ("fall_atr_pct", "log_rvol_pct", "neg_cmf_pct"),
    ),
    "foreign_favorite": (
        "Khối ngoại mua ròng",
        "bullish",
        ("foreign_ratio5_pct", "foreign_ratio20_pct"),
    ),
    "high_dividend": ("Cổ tức cao bền vững", "dividend", ("dividend_yield_pct_rank",)),
    "regular_cash_div": ("Cổ tức tiền mặt đều", "dividend", ("cash_years_pct", "neg_dps_cv_pct")),
    "value_investing": ("Chất lượng & định giá", "value", ("quality", "value")),
}
TECHNICAL = (
    "above_ma20",
    "above_ma50",
    "above_ma200",
    "vol_2x_ma20",
    "rsi_oversold",
    "rsi_overbought",
    "high_volatility",
)


def condition(key, label, keys, predicate, values):
    actual = {name: values.get(name) for name in keys}
    missing = [name for name, value in actual.items() if number(value) is None]
    return {
        "id": key,
        "label": label,
        "values": actual,
        "passed": None if missing else bool(predicate(*actual.values())),
        "missing_fields": missing,
    }


def evaluate(preset, f):
    rows = []

    def add(label, keys, pred):
        rows.append(condition(f"{preset}.{len(rows) + 1}", label, keys, pred, f))

    if preset == "breakout":
        add(
            "Đóng cửa > đỉnh 60 phiên trước + 0,25 ATR",
            ["close", "hh60", "atr14_prev"],
            lambda c, h, a: c > h + 0.25 * a,
        )
        add("Khối lượng ≥ 1,5 lần trung bình 20 phiên trước", ["rvol20"], lambda x: x >= 1.5)
        add("Đóng cửa ở ≥70% biên ngày", ["clv"], lambda x: x >= 0.7)
        add("Giá trên MA50", ["close", "sma50"], lambda c, m: c > m)
        add("Cách MA20 không quá 3 ATR", ["extension"], lambda x: x <= 3)
    elif preset == "strong_trend":
        add(
            "Giá > MA20 > MA50 > MA200",
            ["close", "sma20", "sma50", "sma200"],
            lambda c, a, b, d: c > a > b > d,
        )
        add("Độ dốc MA50 dương", ["slope50"], lambda x: x > 0)
        add("MA200 tăng so với 10 phiên trước", ["sma200", "sma200_10ago"], lambda a, b: a > b)
        add(
            "Sức mạnh tương đối dương, thuộc top 30%",
            ["rs63", "rs63_pct"],
            lambda r, p: r > 0 and p >= 70,
        )
    elif preset == "money_inflow":
        add("Giá tăng so với phiên trước", ["close", "prev_close"], lambda a, b: a > b)
        add("Khối lượng ≥1,5×", ["rvol20"], lambda x: x >= 1.5)
        add("Đóng cửa ở ≥70% biên ngày", ["clv"], lambda x: x >= 0.7)
        add("CMF20 ≥0,10", ["cmf20"], lambda x: x >= 0.1)
    elif preset == "bottom_fishing":
        add("RSI từng dưới 30 trong 5 phiên trước", ["rsi_recent_min"], lambda x: x < 30)
        add("RSI cắt lên 35", ["prev_rsi14", "rsi14"], lambda a, b: a <= 35 < b)
        add("Đóng cửa vượt đỉnh phiên trước", ["close", "prev_high"], lambda a, b: a > b)
        add("Khối lượng ≥1,2×", ["rvol20"], lambda x: x >= 1.2)
    elif preset == "vcp_pattern":
        add("Giá trên MA50", ["close", "sma50"], lambda a, b: a > b)
        add("ATR10/ATR60 ≤0,65", ["contraction"], lambda x: x <= 0.65)
        add(
            "Bollinger width thuộc 20% thấp nhất 126 phiên trước",
            ["bb_percentile"],
            lambda x: x <= 20,
        )
        add(
            "Khối lượng 5 phiên / 20 phiên trước ≤0,75", ["volume_contraction"], lambda x: x <= 0.75
        )
        add("Giá cách đỉnh 60 phiên từ 0–8%", ["distance_high"], lambda x: 0 <= x <= 0.08)
    elif preset == "overbought_peak":
        add("Cao hơn MA20 ≥2,5 ATR", ["extension"], lambda x: x >= 2.5)
        add("RSI14 ≥75", ["rsi14"], lambda x: x >= 75)
    elif preset == "bearish_reversal":
        add("Phiên trước chưa dưới MA20", ["prev_close", "prev_sma20"], lambda a, b: a >= b)
        add("Hôm nay dưới MA20 hơn 0,25 ATR", ["below_ma_atr"], lambda x: x > 0.25)
        add("Khối lượng ≥1,3×", ["rvol20"], lambda x: x >= 1.3)
        add("Đóng cửa ở ≤30% biên ngày", ["clv"], lambda x: x <= 0.3)
    elif preset == "dumping_signal":
        add("Giảm ≥1 ATR so với phiên trước", ["fall_atr"], lambda x: x >= 1)
        add("Khối lượng ≥2×", ["rvol20"], lambda x: x >= 2)
        add("Đóng cửa ở ≤25% biên ngày", ["clv"], lambda x: x <= 0.25)
        add("CMF20 âm", ["cmf20"], lambda x: x < 0)
    elif preset == "foreign_favorite":
        add("Giá trị ngoại ròng 5 phiên ≥2% GT khớp", ["foreign_ratio5"], lambda x: x >= 0.02)
        add("Ít nhất 3/5 phiên mua ròng", ["foreign_positive5"], lambda x: x >= 3)
        add("Tổng mua ròng 20 phiên dương", ["foreign_ratio20"], lambda x: x > 0)
    elif preset in {"high_dividend", "regular_cash_div"}:
        if preset == "high_dividend":
            add(
                "Yield tiền mặt thường xuyên ≥5% và top 25%",
                ["dividend_yield", "dividend_yield_pct_rank"],
                lambda y, r: y >= 0.05 and r >= 75,
            )
        else:
            add("Thực trả tiền mặt ít nhất 3 năm liên tiếp", ["cash_years"], lambda x: x >= 3)
            add("DPS năm gần nhất ≥80% năm trước", ["dps_retention"], lambda x: x >= 0.8)
        add("Payout cùng năm tài chính >0 và ≤80%", ["payout"], lambda x: 0 < x <= 0.8)
        add("CFO 3 năm / tiền cổ tức thực trả ≥1", ["cash_coverage"], lambda x: x >= 1)
        add(
            "Lợi nhuận và CFO gần nhất dương",
            ["dividend_earnings", "latest_cfo"],
            lambda a, b: a > 0 and b > 0,
        )
    elif preset == "value_investing":
        add(
            "EPS, vốn chủ, EBITDA, EV dương",
            ["eps_ttm", "equity", "ebitda_ttm", "enterprise_value"],
            lambda *v: all(x > 0 for x in v),
        )
        add("Chất lượng thuộc top 30% ngành", ["quality_pct"], lambda x: x >= 70)
        add("Định giá thuộc top 30% ngành", ["value_pct"], lambda x: x >= 70)
    elif preset in TECHNICAL:
        if preset.startswith("above_ma"):
            add("Giá trên " + preset[6:].upper(), ["close", "sma" + preset[8:]], lambda c, m: c > m)
        elif preset == "vol_2x_ma20":
            add("Khối lượng >2×", ["rvol20"], lambda x: x > 2)
        elif preset == "rsi_oversold":
            add("RSI <35", ["rsi14"], lambda x: x < 35)
        elif preset == "rsi_overbought":
            add("RSI >70", ["rsi14"], lambda x: x > 70)
        else:
            add("Biên độ / đóng cửa phiên trước >3%", ["high_volatility"], lambda x: x > 0.03)
    else:
        raise ValueError("Unknown preset")
    missing = sorted({key for row in rows for key in row["missing_fields"]})
    score_keys = PRESETS.get(preset, ("", "", ()))[2]
    score_values = {key: f.get(key) for key in score_keys}
    score = average(list(score_values.values()))
    return {
        "status": "unknown" if missing else "evaluated",
        "matched": False if missing else all(row["passed"] for row in rows),
        "conditions": rows,
        "missing_fields": missing,
        "score": round(score, 1) if score is not None else None,
        "score_components": score_values,
        "score_missing_fields": [key for key, value in score_values.items() if value is None],
    }


def catalog():
    return [
        {
            "id": key,
            "label": label,
            "group": group,
            "experimental": group == "experimental",
            "description": " · ".join(row["label"] for row in evaluate(key, {})["conditions"]),
            "formula_version": VERSION,
        }
        for key, (label, group, _) in PRESETS.items()
    ]
