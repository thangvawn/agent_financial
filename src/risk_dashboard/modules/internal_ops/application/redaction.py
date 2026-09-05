from __future__ import annotations

import re
from typing import Any

# Regex patterns for secrets and PII
SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"canary_secret_[a-zA-Z0-9_-]+", re.IGNORECASE), "[REDACTED_CANARY]"),
    (re.compile(r"sk-[a-zA-Z0-9_-]{15,}", re.IGNORECASE), "[REDACTED_API_KEY]"),
    (re.compile(r"ADMIN_[A-Z0-9_]+_KEY=[^\s]+", re.IGNORECASE), "[REDACTED_ENV_SECRET]"),
    (re.compile(r"(?:bearer\s+)[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE), "Bearer [REDACTED_TOKEN]"),
    (re.compile(r"(?:password|passwd|secret)\s*[:=]\s*['\"][^'\"]+['\"]", re.IGNORECASE), "password='[REDACTED_PASSWORD]'"),
]

PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    (re.compile(r"\b(?:\+?84|0)[3|5|7|8|9][0-9]{8}\b"), "[REDACTED_PHONE]"),
    (re.compile(r"\b\d{9}\b|\b\d{12}\b"), "[REDACTED_ID]"),
]


class RedactionEngine:
    @classmethod
    def redact_text(cls, text: str) -> tuple[str, list[str]]:
        if not text or not isinstance(text, str):
            return text, []

        applied_redactions: list[str] = []
        result = text

        for pattern, replacement in SECRET_PATTERNS:
            if pattern.search(result):
                result = pattern.sub(replacement, result)
                applied_redactions.append(replacement.strip("[]"))

        for pattern, replacement in PII_PATTERNS:
            if pattern.search(result):
                result = pattern.sub(replacement, result)
                applied_redactions.append(replacement.strip("[]"))

        return result, list(dict.fromkeys(applied_redactions))

    @classmethod
    def redact_value(cls, val: Any) -> tuple[Any, list[str]]:
        if isinstance(val, str):
            return cls.redact_text(val)
        if isinstance(val, dict):
            new_dict: dict[str, Any] = {}
            all_redactions: list[str] = []
            for k, v in val.items():
                clean_v, reds = cls.redact_value(v)
                new_dict[k] = clean_v
                all_redactions.extend(reds)
            return new_dict, list(dict.fromkeys(all_redactions))
        if isinstance(val, (list, tuple)):
            new_list: list[Any] = []
            all_redactions = []
            for v in val:
                clean_v, reds = cls.redact_value(v)
                new_list.append(clean_v)
                all_redactions.extend(reds)
            return type(val)(new_list), list(dict.fromkeys(all_redactions))
        return val, []

    @classmethod
    def filter_and_redact_dict(
        cls,
        data: dict[str, Any],
        allowlist: set[str] | None = None,
    ) -> tuple[dict[str, Any], list[str]]:
        filtered: dict[str, Any] = {}
        all_redactions: list[str] = []

        for key, val in data.items():
            if allowlist is not None and key not in allowlist:
                continue
            clean_val, reds = cls.redact_value(val)
            filtered[key] = clean_val
            all_redactions.extend(reds)

        return filtered, list(dict.fromkeys(all_redactions))
