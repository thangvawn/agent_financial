"""Safety and compliance policy for the News Intelligence module.

Every API response MUST include a safety block.
The News surface is an event/explanation layer — NOT a trading signal.
"""

from __future__ import annotations

import re
from typing import Any


# ── Safety block constant ───────────────────────────────────────────────

SAFETY_BLOCK: dict[str, Any] = {
    "no_buy_sell_recommendation": True,
    "disclaimer": "Tin tức là bối cảnh phân tích, không phải khuyến nghị mua/bán.",
    "prohibited_ctas": ["buy", "sell", "all_in", "short_now", "long_now"],
    "allowed_ctas": ["read_more", "ask_ai", "save", "learn", "review_exposure", "open_insight"],
}

# ── Buy/sell detection patterns ─────────────────────────────────────────

_UNSAFE_PATTERNS: tuple[str, ...] = (
    r"\b(nên|nen)\s+(mua|bán|ban|long|short)\b",
    r"\b(mua|bán|ban)\s+(ngay|luôn|luon|đi|di)\b",
    r"\ball[\s-]?in\b",
    r"\bshort\s+now\b",
    r"\blong\s+now\b",
    r"\b(mua|buy)\s+mã\b",
    r"\b(bán|sell)\s+hết\b",
    r"\bnên\s+đầu\s+tư\b",
    r"\bkhuyến\s+nghị\b",
)

_UNSAFE_RE = re.compile("|".join(_UNSAFE_PATTERNS), re.IGNORECASE)

REDIRECT_RESPONSE = (
    "Tin này có thể dùng để hiểu bối cảnh và rủi ro, nhưng không đủ để đưa ra lệnh mua/bán. "
    "Tôi có thể giúp bạn phân tích yếu tố ảnh hưởng, kịch bản và điều cần theo dõi."
)


def is_unsafe_query(text: str) -> bool:
    """Detect if user query contains buy/sell/trading intent."""
    return bool(_UNSAFE_RE.search(text))


def build_safety_block() -> dict[str, Any]:
    """Return the standard safety block for API responses."""
    return dict(SAFETY_BLOCK)


# ── Data quality block ──────────────────────────────────────────────────

def build_data_quality_block(
    *,
    freshness: str,
    source_count: int = 0,
    successful_source_count: int = 0,
    stale_reason: str | None = None,
    confidence_label: str = "moderate",
) -> dict[str, Any]:
    """Build the data quality block for API responses."""
    source_health = "healthy"
    if source_count > 0 and successful_source_count < source_count * 0.5:
        source_health = "degraded"
    elif source_count > 0 and successful_source_count < source_count * 0.8:
        source_health = "partial"

    return {
        "freshness": freshness,
        "confidence_label": confidence_label,
        "source_count": source_count,
        "successful_source_count": successful_source_count,
        "source_health": source_health,
        "stale_reason": stale_reason,
    }


def build_analyst_redirect() -> dict[str, Any]:
    """Build a structured redirect when user asks buy/sell questions."""
    return {
        "title": "Không đưa khuyến nghị mua/bán",
        "short_answer": REDIRECT_RESPONSE,
        "explanation": (
            "News Intelligence giúp bạn hiểu bối cảnh thị trường từ tin tức. "
            "Để đưa ra quyết định đầu tư, cần kết hợp nhiều nguồn phân tích khác nhau, "
            "bao gồm dữ liệu tài chính, phân tích kỹ thuật, và đánh giá rủi ro cá nhân."
        ),
        "key_points": [
            "Tin tức là một yếu tố tham khảo, không phải tín hiệu giao dịch.",
            "Tôi có thể giúp phân tích tác động, kịch bản và điều cần theo dõi.",
            "Quyết định đầu tư nên dựa trên nhiều nguồn phân tích.",
        ],
        "why_it_matters": "Đầu tư dựa trên headline đơn lẻ có rủi ro cao.",
        "affected_markets": [],
        "what_to_monitor": [],
        "sources": [],
        "confidence": "high",
        "data_freshness": "n/a",
        "safety_note": SAFETY_BLOCK["disclaimer"],
        "suggested_followups": [
            "Tin này ảnh hưởng tới nhóm tài sản nào?",
            "Có rủi ro gì cần theo dõi?",
            "Giải thích bối cảnh tin này cho tôi.",
        ],
    }
