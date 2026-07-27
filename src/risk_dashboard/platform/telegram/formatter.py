"""HTML formatting primitives for Telegram messages."""

from __future__ import annotations

import html
from typing import Any


def escape_html(text: Any) -> str:
    """Escapes special HTML characters (&, <, >)."""
    return html.escape(str(text), quote=False)


def safe_bold(text: Any) -> str:
    """Wraps escaped text in HTML <b> tags."""
    return f"<b>{escape_html(text)}</b>"


def safe_italic(text: Any) -> str:
    """Wraps escaped text in HTML <i> tags."""
    return f"<i>{escape_html(text)}</i>"


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncates text safely to max_length including suffix if truncated."""
    if len(text) <= max_length:
        return text
    cutoff = max(0, max_length - len(suffix))
    return text[:cutoff] + suffix
