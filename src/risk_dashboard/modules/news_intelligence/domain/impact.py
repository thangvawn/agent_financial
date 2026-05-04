"""Impact mapping for news articles.

Maps article content to affected markets, sectors, monitoring indicators,
and related learning concepts based on keyword analysis.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from risk_dashboard.modules.news_intelligence.domain.enums import LEARN_CONCEPTS, MONITOR_INDICATORS


@dataclass
class ImpactMapping:
    affected_markets: list[str] = field(default_factory=list)
    affected_sectors: list[str] = field(default_factory=list)
    what_to_monitor: list[str] = field(default_factory=list)
    learn_links: list[dict[str, str]] = field(default_factory=list)
    related_entities: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "affected_markets": self.affected_markets,
            "affected_sectors": self.affected_sectors,
            "what_to_monitor": self.what_to_monitor,
            "learn_links": self.learn_links,
            "related_entities": self.related_entities,
        }


# ── Market keyword mapping ─────────────────────────────────────────────

_MARKET_KEYWORDS: dict[str, tuple[str, ...]] = {
    "FX": ("usd", "eur", "jpy", "gbp", "vnd", "fx", "currency", "exchange rate", "tỷ giá", "ngoại tệ", "dollar", "dxy"),
    "Rates": ("rate", "rates", "yield", "bond", "treasury", "lãi suất", "trái phiếu", "fed fund", "fomc"),
    "VN Equity": ("vn-index", "vnindex", "hose", "hnx", "upcom", "cổ phiếu", "chứng khoán việt", "vn stock", "cafef"),
    "US Equity": ("s&p", "nasdaq", "dow", "nyse", "us stock", "wall street", "russell"),
    "Gold": ("gold", "vàng", "xau", "precious metal"),
    "Oil": ("oil", "dầu", "crude", "brent", "wti", "opec", "petroleum"),
    "Banking": ("bank", "ngân hàng", "lending", "tín dụng", "credit", "npl", "deposit"),
    "Real Estate": ("real estate", "bất động sản", "housing", "property", "nhà đất", "mortgage"),
    "Crypto": ("bitcoin", "btc", "ethereum", "eth", "crypto", "stablecoin", "defi", "nft", "blockchain"),
    "Technology": ("ai", "chip", "semiconductor", "nvidia", "openai", "tech", "software", "cloud"),
    "Commodities": ("commodity", "commodities", "hàng hóa", "copper", "steel", "iron", "lithium", "wheat", "corn"),
    "Bonds": ("bond", "treasury", "trái phiếu", "sovereign debt", "government bond"),
}

_SECTOR_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Energy": ("oil", "gas", "energy", "năng lượng", "opec", "renewable", "solar", "wind"),
    "Financials": ("bank", "ngân hàng", "insurance", "fintech", "payment"),
    "Technology": ("ai", "chip", "semiconductor", "software", "cloud", "saas"),
    "Healthcare": ("pharma", "biotech", "healthcare", "vaccine", "fda"),
    "Consumer": ("retail", "consumer", "tiêu dùng", "e-commerce"),
    "Industrial": ("manufacturing", "sản xuất", "construction", "logistics"),
    "Materials": ("mining", "steel", "thép", "chemical", "cement"),
    "Utilities": ("electric", "điện", "water", "nước", "utility"),
}

_MONITOR_KEYWORDS: dict[str, tuple[str, ...]] = {
    "DXY": ("usd", "dollar", "dxy", "greenback"),
    "USD/VND": ("vnd", "tỷ giá", "usd/vnd", "đồng việt nam"),
    "US 10Y Yield": ("yield", "treasury", "10-year", "10y", "bond"),
    "Foreign Flow": ("foreign", "ngoại", "foreign flow", "khối ngoại", "net buy", "net sell"),
    "CPI": ("cpi", "inflation", "lạm phát", "consumer price"),
    "Oil Inventory": ("oil inventory", "crude stock", "eia", "opec"),
    "Fed Speech": ("fed", "fomc", "powell", "federal reserve"),
    "VN-Index": ("vn-index", "vnindex", "hose", "cổ phiếu"),
    "S&P 500": ("s&p", "spx", "sp500"),
    "BTC/USD": ("bitcoin", "btc"),
    "Gold Spot": ("gold", "vàng", "xau"),
    "EUR/USD": ("eur", "euro", "ecb"),
}

_ENTITY_PATTERNS: dict[str, tuple[str, ...]] = {
    "central_bank": ("fed", "federal reserve", "ecb", "boj", "pboc", "rba", "boe", "sbv", "ngân hàng nhà nước"),
    "commodity": ("oil", "gold", "copper", "silver", "wheat", "corn", "natural gas", "iron ore"),
    "currency": ("usd", "eur", "jpy", "gbp", "cny", "vnd", "aud"),
    "country": ("us", "china", "japan", "vietnam", "eu", "india", "russia", "uk", "germany"),
    "macro_indicator": ("cpi", "gdp", "pmi", "nfp", "unemployment", "retail sales", "trade balance"),
}

_LEARN_BY_CATEGORY: dict[str, list[str]] = {
    "macro": ["risk_on_off", "fx_impact", "rate_equity", "bond_yield", "cpi_explained"],
    "commodities": ["oil_inflation", "fx_impact"],
    "crypto": ["crypto_liquidity", "risk_on_off"],
    "markets": ["rate_equity", "risk_on_off", "bond_yield"],
    "earnings": ["earnings_reading"],
    "geopolitics": ["geopolitics_market", "risk_on_off"],
    "regulation": ["risk_on_off"],
    "technology": ["risk_on_off"],
}

_LEARN_BY_ID = {concept["id"]: concept for concept in LEARN_CONCEPTS}


def map_impact(*, headline: str, summary: str, category: str) -> ImpactMapping:
    """Map article content to affected markets, sectors, monitors, and learn links."""
    text = f"{headline} {summary}".lower()

    affected_markets = _match_keywords(text, _MARKET_KEYWORDS, limit=6)
    affected_sectors = _match_keywords(text, _SECTOR_KEYWORDS, limit=4)
    what_to_monitor = _match_keywords(text, _MONITOR_KEYWORDS, limit=5)
    related_entities = _extract_entities(text)
    learn_links = _resolve_learn_links(category)

    # If no specific monitors found, infer from category
    if not what_to_monitor:
        what_to_monitor = _default_monitors_for_category(category)

    return ImpactMapping(
        affected_markets=affected_markets,
        affected_sectors=affected_sectors,
        what_to_monitor=what_to_monitor,
        learn_links=learn_links,
        related_entities=related_entities,
    )


def _match_keywords(text: str, keyword_map: dict[str, tuple[str, ...]], *, limit: int) -> list[str]:
    """Match text against keyword groups, return matched group names."""
    matches: list[tuple[str, int]] = []
    for label, keywords in keyword_map.items():
        hit_count = sum(1 for kw in keywords if kw in text)
        if hit_count > 0:
            matches.append((label, hit_count))
    matches.sort(key=lambda x: x[1], reverse=True)
    return [m[0] for m in matches[:limit]]


def _extract_entities(text: str) -> list[dict[str, str]]:
    """Extract named entities from text."""
    entities: list[dict[str, str]] = []
    seen: set[str] = set()
    for entity_type, patterns in _ENTITY_PATTERNS.items():
        for pattern in patterns:
            if pattern in text and pattern not in seen:
                seen.add(pattern)
                entities.append({"type": entity_type, "name": pattern, "confidence": "rule_based"})
    # Also extract uppercase tickers (2-5 chars)
    blocked = {"THE", "AND", "FOR", "WITH", "FROM", "FED", "SEC", "ECB", "IMF", "GDP", "CPI", "CEO", "ETF", "RSS"}
    for match in re.finditer(r"\b[A-Z]{2,5}\b", f"{text}"):
        ticker = match.group(0)
        if ticker not in blocked and ticker not in seen:
            seen.add(ticker)
            entities.append({"type": "ticker", "name": ticker, "confidence": "regex"})
            if len(entities) >= 12:
                break
    return entities[:10]


def _resolve_learn_links(category: str) -> list[dict[str, str]]:
    """Return relevant learn concept links based on category."""
    concept_ids = _LEARN_BY_CATEGORY.get(category, ["risk_on_off"])
    links: list[dict[str, str]] = []
    for concept_id in concept_ids[:3]:
        concept = _LEARN_BY_ID.get(concept_id)
        if concept:
            links.append({"id": concept["id"], "label": concept["label"]})
    return links


def _default_monitors_for_category(category: str) -> list[str]:
    """Fallback monitors when keyword matching finds nothing."""
    defaults: dict[str, list[str]] = {
        "macro": ["DXY", "US 10Y Yield", "Fed Speech"],
        "commodities": ["Oil Inventory", "Gold Spot", "DXY"],
        "crypto": ["BTC/USD", "DXY", "US 10Y Yield"],
        "markets": ["S&P 500", "VN-Index", "Foreign Flow"],
        "regulation": ["S&P 500", "BTC/USD"],
        "geopolitics": ["Gold Spot", "Oil Inventory", "DXY"],
        "technology": ["S&P 500", "BTC/USD"],
        "earnings": ["S&P 500", "VN-Index"],
    }
    return defaults.get(category, ["DXY", "S&P 500"])
