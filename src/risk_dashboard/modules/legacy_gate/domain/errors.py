"""Domain errors for legacy gate."""
from __future__ import annotations

from typing import Literal

LegacyGateErrorType = Literal[
    "module_not_found",
    "gate_not_ready",
    "missing_baseline",
    "decision_required",
    "approval_required",
    "already_reactivated",
]


class LegacyGateError(Exception):
    """Base domain exception for Legacy Gate operations."""

    def __init__(
        self,
        message: str,
        error_type: LegacyGateErrorType,
        module_slug: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.module_slug = module_slug

    def __str__(self) -> str:
        prefix = f"[{self.error_type}]"
        if self.module_slug:
            prefix += f" ({self.module_slug})"
        return f"{prefix} {self.message}"

