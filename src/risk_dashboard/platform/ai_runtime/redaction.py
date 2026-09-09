from __future__ import annotations

import re

from risk_dashboard.platform.ai_runtime.contracts import ModelMessage, ModelTask

_SECRET_PATTERNS = (
    # Key-value secret assignments
    re.compile(r"(?i)(api[_-]?key|token|password|secret|client[_-]?secret)\s*[:=]\s*[^\s,;]+"),
    # Bearer tokens
    re.compile(r"(?i)bearer\s+[a-z0-9._-]+"),
    # Google API Key
    re.compile(r"AIza[0-9A-Za-z-_]{30,45}"),
    # OpenAI API Keys (legacy & project-scoped)
    re.compile(r"sk-(?:proj-)?[a-zA-Z0-9_-]{20,}"),
    # GitHub Personal Access / App Tokens
    re.compile(r"gh[pousr]_[a-zA-Z0-9]{36,}"),
    re.compile(r"github_pat_[a-zA-Z0-9_]{22,}"),
    # AWS Access Key IDs
    re.compile(r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}"),
    # Slack Tokens
    re.compile(r"xox[baprs]-[0-9a-zA-Z-]{10,}"),
    # JSON Web Tokens (JWT)
    re.compile(r"eyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*"),
    # PEM Private Key and Certificate blocks
    re.compile(r"-----BEGIN [A-Z0-9_ -]+-----[\s\S]*?-----END [A-Z0-9_ -]+-----"),
)

_PII_PATTERNS = (
    # Email addresses
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    # Vietnamese mobile phone numbers (supports +84/0 with optional spaces, dots, dashes)
    re.compile(r"(?:(?<!\w)(?:\+84[\s.-]?|0))[35789](?:[\s.-]?[0-9]){8}\b"),
    # Vietnamese Citizen ID (CCCD 12-digit)
    re.compile(r"(?<!\w)0[0-9]{2}(?:[\s.-]?[0-9]{3}){3}\b|(?<!\w)0[0-9]{11}\b"),
)




def contains_secrets(value: str) -> bool:
    """Check whether a text string contains known raw secrets or credentials."""
    return any(pattern.search(value) is not None for pattern in _SECRET_PATTERNS)


def contains_pii(value: str) -> bool:
    """Check whether a text string contains personally identifiable information."""
    return any(pattern.search(value) is not None for pattern in _PII_PATTERNS)


def redact_text(value: str) -> str:
    """Redact all detected secrets and credentials, and mask PII as [REDACTED_PII]."""
    redacted = value
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    for pattern in _PII_PATTERNS:
        redacted = pattern.sub("[REDACTED_PII]", redacted)
    return redacted


def redact_for_provider(task: ModelTask) -> ModelTask:
    """Return a copy of ModelTask with all message contents safely redacted."""
    return task.model_copy(
        update={
            "messages": tuple(
                ModelMessage(role=message.role, content=redact_text(message.content))
                for message in task.messages
            )
        }
    )
