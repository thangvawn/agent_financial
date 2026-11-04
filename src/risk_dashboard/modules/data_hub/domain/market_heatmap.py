"""A coherent, read-only universe for a Vietnamese market heatmap.

Price/value are VND, market cap is billion VND, volume is shares, matching
VnMarketFeedProducer's quote contract. No inferred capitalisation or quotes.
"""

from __future__ import annotations

import math
import re

SECTORS = {
    "0": "Dầu khí",
    "1": "Nguyên vật liệu",
    "2": "Công nghiệp",
    "3": "Hàng tiêu dùng",
    "4": "Y tế",
    "5": "Dịch vụ tiêu dùng",
    "6": "Viễn thông",
    "7": "Tiện ích",
    "8": "Tài chính",
    "9": "Công nghệ",
    "real_estate": "Bất động sản",
    "unknown": "Chưa phân ngành",
}
NUMBERS = ("price", "ref_price", "ceiling", "floor", "change_pct", "value", "volume", "market_cap")


def finite_number(value):
    if value is None or isinstance(value, bool) or value == "":
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (ValueError, TypeError):
        return None


def heatmap_items(quotes: list[dict]) -> list[dict]:
    result = {}
    for row in quotes:
        symbol = str(row.get("symbol") or "").strip().upper()
        if not re.fullmatch(r"[A-Z0-9]{2,12}", symbol):
            continue
        code = str(row.get("industry_code") or "")
        sector = (
            "real_estate"
            if code == "8630"
            else code[:1]
            if re.fullmatch(r"\d{4}", code)
            else "unknown"
        )
        numbers = {key: finite_number(row.get(key)) for key in NUMBERS}
        for key in NUMBERS:
            if key != "change_pct" and numbers[key] is not None and numbers[key] < 0:
                numbers[key] = None
        result[symbol] = {
            "symbol": symbol,
            "name": str(row.get("name") or symbol)[:240],
            "exchange": str(row.get("exchange") or "").upper().replace("HSX", "HOSE"),
            "sector_id": sector,
            "sector": SECTORS.get(sector, SECTORS["unknown"]),
            "industry_code": code or None,
            "industry": row.get("industry"),
            **numbers,
        }
    return sorted(result.values(), key=lambda row: row["symbol"])
