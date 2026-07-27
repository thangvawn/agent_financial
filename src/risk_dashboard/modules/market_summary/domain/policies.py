"""Session completion policies and data quality validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class CompletionResult:
    is_complete: bool
    retry_recommended: bool
    reason: str
    missing_fields: list[str] = field(default_factory=list)


class SessionCompletionPolicy:
    """Validates if market data for expected_date is closed and complete."""

    def __init__(self, min_advancers_decliners_total: int = 100) -> None:
        self.min_advancers_decliners_total = min_advancers_decliners_total

    def validate(
        self,
        vnindex_latest_date: date,
        expected_date: date,
        vnindex_close: float,
        vnindex_volume: int,
        total_breadth_stocks: int,
    ) -> CompletionResult:
        missing: list[str] = []

        if vnindex_latest_date != expected_date:
            return CompletionResult(
                is_complete=False,
                retry_recommended=True,
                reason=f"Data date mismatch: latest available is {vnindex_latest_date}, expected {expected_date}",
                missing_fields=["trading_date"],
            )

        if vnindex_close <= 0:
            missing.append("vnindex_close")

        if vnindex_volume <= 0:
            missing.append("vnindex_volume")

        if total_breadth_stocks < self.min_advancers_decliners_total:
            missing.append("market_breadth")

        if missing:
            return CompletionResult(
                is_complete=False,
                retry_recommended=True,
                reason=f"Incomplete session metrics: missing or invalid fields: {', '.join(missing)}",
                missing_fields=missing,
            )

        return CompletionResult(
            is_complete=True,
            retry_recommended=False,
            reason="Session data is complete and valid.",
        )
