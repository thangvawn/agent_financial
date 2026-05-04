from __future__ import annotations

import re

from risk_dashboard.modules.news_intelligence.domain.entities import NewsArticle


POSITIVE_WORDS = {
    "gain",
    "gains",
    "rally",
    "rises",
    "beats",
    "growth",
    "strong",
    "optimism",
    "surge",
    "record",
    "eases",
}
NEGATIVE_WORDS = {
    "fall",
    "falls",
    "drop",
    "drops",
    "miss",
    "weak",
    "recession",
    "inflation",
    "war",
    "risk",
    "selloff",
    "default",
    "cuts",
}
HIGH_PRIORITY_WORDS = {"fed", "rate", "inflation", "war", "oil", "tariff", "earnings", "sec", "ecb", "imf", "bitcoin"}
SYSTEMIC_RISK_WORDS = {"crisis", "default", "bank run", "sanction", "invasion", "recession", "liquidity"}
TICKER_RE = re.compile(r"\b[A-Z]{2,5}\b")


def enrich_article(article: NewsArticle) -> NewsArticle:
    text = f"{article.headline} {article.summary}".lower()
    article.language = _detect_language(text)
    article.priority = _priority(text, article.source_tier)
    article.sentiment = _sentiment(text)
    article.impact = _impact(article.priority, article.source_tier)
    article.category = _refine_category(article.category, text)
    article.tickers = _extract_tickers(article.headline)
    article.threat_level, article.threat_category, article.threat_confidence = _threat(text)
    return article


def _detect_language(text: str) -> str:
    vietnamese_marks = ("đ", "ă", "â", "ê", "ô", "ơ", "ư")
    return "vi" if any(mark in text for mark in vietnamese_marks) else "en"


def _priority(text: str, source_tier: int) -> int:
    score = 2 if source_tier <= 2 else 1
    score += sum(1 for word in HIGH_PRIORITY_WORDS if word in text)
    return max(1, min(5, score))


def _sentiment(text: str) -> str:
    positive = sum(1 for word in POSITIVE_WORDS if word in text)
    negative = sum(1 for word in NEGATIVE_WORDS if word in text)
    if positive > negative + 1:
        return "positive"
    if negative > positive + 1:
        return "negative"
    return "neutral"


def _impact(priority: int, source_tier: int) -> str:
    if priority >= 4 and source_tier <= 2:
        return "high"
    if priority >= 3:
        return "medium"
    return "low"


def _refine_category(default: str, text: str) -> str:
    if any(word in text for word in ("fed", "ecb", "rate", "inflation", "cpi", "gdp", "imf")):
        return "macro"
    if any(word in text for word in ("oil", "gold", "copper", "commodity", "brent", "wti")):
        return "commodities"
    if any(word in text for word in ("bitcoin", "crypto", "ethereum", "stablecoin")):
        return "crypto"
    if any(word in text for word in ("earnings", "stocks", "shares", "market", "nasdaq", "s&p")):
        return "markets"
    if any(word in text for word in ("sec", "regulator", "lawsuit", "fine")):
        return "regulation"
    return default


def _extract_tickers(headline: str) -> list[str]:
    blocked = {"THE", "AND", "FOR", "WITH", "FROM", "FED", "SEC", "ECB", "IMF", "GDP", "CPI", "CEO", "ETF"}
    tickers = [match.group(0) for match in TICKER_RE.finditer(headline)]
    return sorted({ticker for ticker in tickers if ticker not in blocked})[:8]


def _threat(text: str) -> tuple[str, str | None, float]:
    hits = [word for word in SYSTEMIC_RISK_WORDS if word in text]
    if not hits:
        return "normal", None, 0.0
    if len(hits) >= 2:
        return "elevated", "systemic_risk", 0.75
    return "watch", "market_risk", 0.45

