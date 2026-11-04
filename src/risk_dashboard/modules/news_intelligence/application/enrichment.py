from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import datetime, timezone

from risk_dashboard.modules.news_intelligence.domain.entities import NewsArticle
from risk_dashboard.modules.news_intelligence.domain.impact import map_impact
from risk_dashboard.modules.news_intelligence.domain.scoring import calculate_importance
from risk_dashboard.modules.news_intelligence.domain.text import (
    contains_keyword,
    count_keywords,
    normalize_text,
)
from risk_dashboard.modules.news_intelligence.domain.time import parse_utc_datetime

POSITIVE_WORDS = {
    "tăng trưởng", "tăng mạnh", "tăng kỷ lục", "khởi sắc", "phục hồi",
    "vượt kỳ vọng", "vượt kế hoạch", "bứt phá", "lãi kỷ lục",
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
    "giảm mạnh", "lao dốc", "sụt giảm", "thua lỗ", "phá sản", "vỡ nợ",
    "suy thoái", "bán tháo", "khủng hoảng", "đình trệ", "thất thoát",
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

VIETNAMESE_MARKERS = {
    "thi truong",
    "ngan hang",
    "chung khoan",
    "lai suat",
    "lam phat",
    "ty gia",
    "doanh nghiep",
    "kinh te",
    "tang truong",
    "viet nam",
    "co phieu",
    "bat dong san",
    "dau tu",
}


def enrich_article(article: NewsArticle) -> NewsArticle:
    text = f"{article.headline} {article.summary}"
    article.language = _detect_language(text)
    article.priority = _priority(text, article.source_tier)
    article.sentiment = _sentiment(text)
    article.impact = _impact(article.priority, article.source_tier)
    article.category = _refine_category(article.category, text)
    article.tickers = _extract_tickers(article.headline)
    article.threat_level, article.threat_category, article.threat_confidence = _threat(text)
    article.content_hash = _content_hash(article.headline, article.url)
    article.source_mix = getattr(article, "source_mix", "") or ""

    # ── Importance scoring ──
    published_at = parse_utc_datetime(article.published_at)
    if published_at is None:
        age_minutes = 60.0
    else:
        # Clock skew from a publisher must not make a future article more
        # valuable than a genuinely fresh one.
        age_minutes = max(0.0, (datetime.now(timezone.utc) - published_at).total_seconds() / 60)
    importance = calculate_importance(
        headline=article.headline,
        summary=article.summary,
        source_tier=article.source_tier,
        impact=article.impact,
        sentiment=article.sentiment,
        threat_level=article.threat_level,
        age_minutes=max(0, age_minutes),
    )
    article.importance_score = importance.score
    article.importance_label = importance.label
    article.importance_breakdown = importance.breakdown.to_dict()

    # ── Impact mapping ──
    impact_mapping = map_impact(headline=article.headline, summary=article.summary, category=article.category)
    article.affected_markets = impact_mapping.affected_markets
    article.affected_sectors = impact_mapping.affected_sectors
    article.what_to_monitor = impact_mapping.what_to_monitor
    article.learn_links = impact_mapping.learn_links
    article.related_entities = impact_mapping.related_entities

    return article


def _detect_language(text: str) -> str:
    vietnamese_marks = ("đ", "ă", "â", "ê", "ô", "ơ", "ư")
    normalized = normalize_text(text)
    return "vi" if any(mark in text.lower() for mark in vietnamese_marks) or any(
        contains_keyword(normalized, marker) for marker in VIETNAMESE_MARKERS
    ) else "en"


def _priority(text: str, source_tier: int) -> int:
    score = 2 if source_tier <= 2 else 1
    score += count_keywords(text, HIGH_PRIORITY_WORDS)
    return max(1, min(5, score))


def _sentiment(text: str) -> str:
    text = unicodedata.normalize("NFC", text).casefold()

    def evidence(words: set[str]) -> int:
        count = 0
        for word in words:
            for match in re.finditer(rf"(?<!\w){re.escape(word)}(?!\w)", text):
                # Negated evidence is uncertain, not automatically opposite sentiment.
                clause = re.split(r"[.!?;,\n]", text[:match.start()])[-1]
                prefix = clause.split()[-3:]
                # A direction in inflation, rates or costs is not an equity sentiment.
                if word in {"tăng mạnh", "giảm mạnh"} and any(
                    contains_keyword(clause, subject)
                    for subject in ("lạm phát", "lãi suất", "chi phí", "nợ xấu", "giá dầu")
                ):
                    continue
                if not {"không", "chưa", "chẳng", "not", "no", "without"}.intersection(prefix):
                    count += 1
                    break
        return count

    positive = evidence(POSITIVE_WORDS)
    negative = evidence(NEGATIVE_WORDS)
    if positive > negative:
        return "positive"
    if negative > positive:
        return "negative"
    if not positive and not negative and evidence({"ổn định", "không đổi", "unchanged", "stable"}):
        return "neutral"
    return "unknown"


def _impact(priority: int, source_tier: int) -> str:
    if priority >= 4 and source_tier <= 2:
        return "high"
    if priority >= 3:
        return "medium"
    return "low"


def _refine_category(default: str, text: str) -> str:
    if any(contains_keyword(text, word) for word in ("fed", "ecb", "rate", "rates", "inflation", "cpi", "gdp", "imf", "lãi suất", "lạm phát")):
        return "macro"
    if any(contains_keyword(text, word) for word in ("oil", "gold", "copper", "commodity", "brent", "wti", "dầu", "vàng")):
        return "commodities"
    if any(contains_keyword(text, word) for word in ("bitcoin", "crypto", "ethereum", "stablecoin")):
        return "crypto"
    if any(contains_keyword(text, word) for word in ("earnings", "stocks", "shares", "market", "nasdaq", "s&p", "cổ phiếu", "chứng khoán")):
        return "markets"
    if any(contains_keyword(text, word) for word in ("sec", "regulator", "lawsuit", "fine", "pháp lý")):
        return "regulation"
    return default


def _extract_tickers(headline: str) -> list[str]:
    blocked = {"THE", "AND", "FOR", "WITH", "FROM", "FED", "SEC", "ECB", "IMF", "GDP", "CPI", "CEO", "ETF"}
    tickers = [match.group(0) for match in TICKER_RE.finditer(headline)]
    return sorted({ticker for ticker in tickers if ticker not in blocked})[:8]


def _threat(text: str) -> tuple[str, str | None, float]:
    hits = [word for word in SYSTEMIC_RISK_WORDS if contains_keyword(text, word)]
    if not hits:
        return "normal", None, 0.0
    if len(hits) >= 2:
        return "elevated", "systemic_risk", 0.75
    return "watch", "market_risk", 0.45


def _content_hash(headline: str, url: str) -> str:
    return hashlib.sha256(f"{headline.strip().lower()}|{url}".encode()).hexdigest()[:32]
