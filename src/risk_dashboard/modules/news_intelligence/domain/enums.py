"""Canonical enums and constants for the News Intelligence module."""

from __future__ import annotations


# ── Importance ──────────────────────────────────────────────────────────

class ImportanceLabel:
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NOISE = "noise"


IMPORTANCE_THRESHOLDS: list[tuple[int, str]] = [
    (85, ImportanceLabel.CRITICAL),
    (70, ImportanceLabel.HIGH),
    (50, ImportanceLabel.MEDIUM),
    (30, ImportanceLabel.LOW),
]


def importance_label_for_score(score: int) -> str:
    for threshold, label in IMPORTANCE_THRESHOLDS:
        if score >= threshold:
            return label
    return ImportanceLabel.NOISE


# ── Categories ──────────────────────────────────────────────────────────

CATEGORIES: tuple[str, ...] = (
    "macro",
    "markets",
    "commodities",
    "crypto",
    "regulation",
    "geopolitics",
    "technology",
    "earnings",
    "personal_finance",
    "risk_alerts",
)

# ── Regions ─────────────────────────────────────────────────────────────

REGIONS: tuple[str, ...] = ("VN", "US", "global", "EU", "Asia")

# ── Source Mix ──────────────────────────────────────────────────────────

SOURCE_MIX_VALUES: tuple[str, ...] = (
    "official",
    "vn_markets",
    "vn_macro",
    "us_markets",
    "global_macro",
    "global_markets",
    "commodities_energy",
    "crypto",
    "technology",
)

# ── Sentiment ───────────────────────────────────────────────────────────

class Sentiment:
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


# ── Impact Level ────────────────────────────────────────────────────────

class ImpactLevel:
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ── Threat Level ────────────────────────────────────────────────────────

class ThreatLevel:
    NORMAL = "normal"
    WATCH = "watch"
    ELEVATED = "elevated"
    CRITICAL = "critical"


# ── Affected Markets ───────────────────────────────────────────────────

AFFECTED_MARKET_TAGS: tuple[str, ...] = (
    "FX",
    "Rates",
    "VN Equity",
    "US Equity",
    "Gold",
    "Oil",
    "Banking",
    "Real Estate",
    "Crypto",
    "Technology",
    "Commodities",
    "Bonds",
)

# ── Monitor Indicators ─────────────────────────────────────────────────

MONITOR_INDICATORS: tuple[str, ...] = (
    "DXY",
    "USD/VND",
    "US 10Y Yield",
    "Foreign Flow",
    "CPI",
    "Oil Inventory",
    "Fed Speech",
    "VN-Index",
    "S&P 500",
    "BTC/USD",
    "Gold Spot",
    "EUR/USD",
)

# ── Learn Concepts ──────────────────────────────────────────────────────

LEARN_CONCEPTS: tuple[dict[str, str], ...] = (
    {"id": "risk_on_off", "label": "Risk-on / Risk-off là gì?", "category": "macro"},
    {"id": "fx_impact", "label": "Tỷ giá ảnh hưởng thị trường thế nào?", "category": "macro"},
    {"id": "rate_equity", "label": "Lãi suất ảnh hưởng cổ phiếu ra sao?", "category": "macro"},
    {"id": "oil_inflation", "label": "Giá dầu và lạm phát", "category": "commodities"},
    {"id": "cpi_explained", "label": "CPI là gì?", "category": "macro"},
    {"id": "bond_yield", "label": "Yield trái phiếu nói gì về kỳ vọng?", "category": "macro"},
    {"id": "crypto_liquidity", "label": "Crypto và thanh khoản toàn cầu", "category": "crypto"},
    {"id": "earnings_reading", "label": "Đọc báo cáo lợi nhuận cơ bản", "category": "earnings"},
    {"id": "geopolitics_market", "label": "Rủi ro địa chính trị ảnh hưởng thị trường", "category": "geopolitics"},
)
