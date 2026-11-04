"""Shared text helpers for deterministic News classification.

News headlines arrive from a mix of English and Vietnamese feeds.  Keeping
normalisation and keyword matching in one place prevents each classifier from
making subtly different substring decisions (for example treating ``war`` as
present in ``hardware``).
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)


def normalize_text(value: str) -> str:
    """Return case-folded, accent-insensitive text with stable whitespace."""

    text = unicodedata.normalize("NFKD", value or "")
    # Vietnamese đ/Đ are not decomposed by NFKD.
    text = text.replace("đ", "d").replace("Đ", "D")
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.casefold().split())


def tokens(value: str) -> set[str]:
    """Extract unicode word tokens after normalisation."""

    return set(_TOKEN_RE.findall(normalize_text(value)))


def contains_keyword(value: str, keyword: str) -> bool:
    """Match a whole word or phrase, without substring false positives."""

    # Classification must preserve Vietnamese meaning: đầu != dầu, tăng != tang.
    # Accent folding remains available to search/clustering through normalize_text.
    text = unicodedata.normalize("NFC", value or "").casefold()
    needle = unicodedata.normalize("NFC", keyword or "").casefold()
    if not needle:
        return False
    # Match the meaningful words while allowing punctuation in symbols such
    # as S&P, VN-Index, or USD/VND.  Word boundaries prevent ``war`` from
    # matching ``hardware``.
    parts = _TOKEN_RE.findall(needle)
    if not parts:
        return False
    joined = r"[\W_]+".join(re.escape(part) for part in parts)
    pattern = rf"(?<!\w){joined}(?!\w)"
    return re.search(pattern, text, flags=re.UNICODE) is not None


def count_keywords(value: str, keywords: Iterable[str]) -> int:
    """Count distinct keyword groups present in ``value``."""

    return sum(1 for keyword in keywords if contains_keyword(value, keyword))


def matching_keywords(value: str, keywords: Iterable[str]) -> list[str]:
    """Return matching keywords in caller-provided order."""

    return [keyword for keyword in keywords if contains_keyword(value, keyword)]
