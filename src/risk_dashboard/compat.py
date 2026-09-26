"""Small standard-library compatibility helpers.

The application supports Python 3.10, while :class:`enum.StrEnum` was
introduced in Python 3.11.  Keep the fallback in one place so enum values have
the same string behaviour on every supported interpreter.
"""

from enum import Enum

try:  # pragma: no cover - exercised implicitly on Python 3.11+
    from enum import StrEnum  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - covered by the Python 3.10 CI job
    class StrEnum(str, Enum):
        """Backport of ``enum.StrEnum`` for Python 3.10."""

        def __str__(self) -> str:
            return self.value


__all__ = ["StrEnum"]
