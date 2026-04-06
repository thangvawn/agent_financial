from __future__ import annotations

from enum import Enum


class Intent(str, Enum):
    explain = "explain"
    what_if = "what_if"
    historical_sector = "historical_sector"
    chitchat = "chitchat"


def route_intent(message: str) -> Intent:
    m = message.lower()
    if any(k in m for k in ("nếu", "what if", "giả sử", "can thiệp", "ép tỷ giá", "mô phỏng")):
        return Intent.what_if
    if any(k in m for k in ("ngành", "lịch sử", "sector", "nhóm ngành", "phòng thủ")):
        return Intent.historical_sector
    if any(k in m for k in ("shap", "tại sao", "giải thích", "rủi ro", "bao nhiêu")):
        return Intent.explain
    return Intent.chitchat
