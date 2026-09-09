from __future__ import annotations

import logging
import re

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
API_KEY_PATTERN = re.compile(r"\b(?:sk|pk|key|secret)[-_a-zA-Z0-9]{10,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"\b(?:\+?84|0)[3|5|7|8|9][0-9]{8}\b")


def redact_pii(text: str) -> str:
    """Scrub sensitive PII and secrets from text."""
    if not isinstance(text, str):
        return text

    scrubbed = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
    scrubbed = API_KEY_PATTERN.sub("[REDACTED_KEY]", scrubbed)
    scrubbed = PHONE_PATTERN.sub("[REDACTED_PHONE]", scrubbed)
    return scrubbed


class PIIFilter(logging.Filter):
    """Logging filter that scrubs sensitive PII before writing logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_pii(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: redact_pii(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(redact_pii(str(v)) for v in record.args)
        return True

