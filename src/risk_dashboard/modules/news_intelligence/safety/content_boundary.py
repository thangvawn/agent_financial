from __future__ import annotations

import html
from html.parser import HTMLParser
import re
from dataclasses import dataclass
from typing import Any

MAX_ARTICLE_TEXT_LENGTH = 5000

_UNSAFE_TAGS = frozenset({"script", "style", "iframe", "object", "embed", "applet", "meta", "link"})


class _TextExtractingSanitizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._pieces: list[str] = []
        self._unsafe_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in _UNSAFE_TAGS:
            self._unsafe_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in _UNSAFE_TAGS and self._unsafe_depth > 0:
            self._unsafe_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._unsafe_depth == 0:
            self._pieces.append(data)

    def get_text(self) -> str:
        return "".join(self._pieces)


_INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("ignore_instructions", re.compile(r"\b(ignore|bỏ\s*qua|quên)\s+(all\s+)?(previous|trước|mọi)\s+(instructions|prompts|chỉ\s*thị|hướng\s*dẫn)\b", re.IGNORECASE)),
    ("system_prompt", re.compile(r"\b(system\s*prompt|prompt\s*hệ\s*thống|you\s+are\s+now|bạn\s+bây\s+giờ\s+là)\b", re.IGNORECASE)),
    ("call_tool_override", re.compile(r"\b(call\s+tool|gọi\s+tool|execute\s+tool|save_brief|update_progress|grant\s+scope)\b", re.IGNORECASE)),
    ("jailbreak_dan", re.compile(r"\b(DAN\s+mode|jailbreak|bẻ\s*khóa|unrestricted\s+mode)\b", re.IGNORECASE)),
    ("save_data_injection", re.compile(r"\b(save\s+data|save\s+brief\s+with\s+my\s+data|lưu\s+dữ\s+liệu\s+này)\b", re.IGNORECASE)),
    ("role_reversal", re.compile(r"\b(acting\s+as\s+admin|quyền\s+admin|root\s+access|bypass\s+policy)\b", re.IGNORECASE)),
    ("exfiltration_url", re.compile(r"\b(send\s+to\s+http|fetch\s+http|exfiltrate|gửi\s+tới\s+url)\b", re.IGNORECASE)),
)


@dataclass(frozen=True)
class TaintedContent:
    text: str
    is_untrusted_content: bool = True
    detected_injections: tuple[str, ...] = ()
    sanitized: bool = True

    def __str__(self) -> str:
        return self.text


def sanitize_article_content(raw_text: str, max_length: int = MAX_ARTICLE_TEXT_LENGTH) -> str:
    """Robustly parse HTML, strip scripts/unsafe elements, and enforce length limit."""
    if not raw_text:
        return ""

    # Parse and extract safe text
    parser = _TextExtractingSanitizer()
    try:
        parser.feed(raw_text)
        parser.close()
        cleaned = parser.get_text()
    except Exception:
        # Fallback regex strip if HTML parsing encounters malformed anomalies
        cleaned = re.sub(r"<[^>]+>", " ", raw_text)

    # Decode HTML entities and clean Javascript URI attempts
    cleaned = html.unescape(cleaned)
    cleaned = re.sub(r"javascript:\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length] + "... [truncated]"

    return cleaned


def detect_injection_patterns(text: str) -> list[str]:
    """Scan text against indirect prompt injection patterns."""
    if not text:
        return []
    matched: list[str] = []
    for name, pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            matched.append(name)
    return matched


def taint_label(text: str) -> TaintedContent:
    """Sanitize and wrap untrusted article text in a TaintedContent container."""
    sanitized = sanitize_article_content(text)
    injections = detect_injection_patterns(sanitized)
    return TaintedContent(
        text=sanitized,
        is_untrusted_content=True,
        detected_injections=tuple(injections),
        sanitized=True,
    )
