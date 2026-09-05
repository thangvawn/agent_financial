"""Domain errors for quant_research module."""
from __future__ import annotations

from typing import Literal


class QuantAdapterError(Exception):
    """Typed error for quant adapter operations."""

    def __init__(
        self,
        error_type: Literal[
            "invalid_input",
            "panel_unavailable",
            "date_out_of_range",
            "model_unavailable",
            "engine_failure",
            "deadline_exceeded",  # Reserved for Phase QF5 (timeout / SLA breaches)
            "numeric_review_failed",  # Reserved for Phase QF5 (strict rejection mode)
        ],
        message: str,
        *,
        hint: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.hint = hint
        self.cause = cause
