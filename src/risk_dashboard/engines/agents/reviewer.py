from __future__ import annotations

import re

from risk_dashboard.schemas.snapshots import QuantEngineOutput, ReviewResult


def _must_appear(value: float, text: str, *, decimals: int) -> bool:
    s = f"{value:.{decimals}f}"
    return s in text


def verify_narrative_against_quant(text: str, q: QuantEngineOutput) -> ReviewResult:
    """Kiểm tra các con số cốt lõi trong narrative có khớp quant không."""
    mismatches: list[str] = []
    p2 = q.horizons.p_decline_2w * 100.0
    if not _must_appear(p2, text, decimals=1):
        mismatches.append(f"p_decline_2w_pct {p2:.1f} not found verbatim")
    dd = q.horizons.expected_drawdown_pct
    if not _must_appear(dd, text, decimals=2):
        mismatches.append(f"expected_drawdown_pct {dd:.2f} not found verbatim")
    vn = float(q.narrative_inputs.get("vn_index", 0.0))
    if not _must_appear(vn, text, decimals=2):
        mismatches.append(f"vn_index {vn:.2f} not found verbatim")
    # Tỷ giá: cho phép có dấu phẩy hoặc không
    fx = float(q.narrative_inputs.get("usd_vnd_rate", 0.0))
    if f"{fx:.2f}" not in text and f"{fx:.0f}" not in text:
        mismatches.append(f"usd_vnd_rate {fx} not found in text")
    return ReviewResult(ok=len(mismatches) == 0, mismatches=mismatches)


def extract_assumption_number(user_message: str) -> float | None:
    """Bắt số tỷ giả định dạng 25000 / 25.000 — dùng cho simulation đơn giản."""
    m = re.search(r"25[.,]?\d{3}", user_message)
    if not m:
        m = re.search(r"\b\d{4,6}\b", user_message)
    if not m:
        return None
    raw = m.group(0).replace(".", "").replace(",", "")
    try:
        return float(raw)
    except ValueError:
        return None
