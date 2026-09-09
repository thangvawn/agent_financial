from __future__ import annotations

import os

from risk_dashboard.platform.feature_flags.decorator import feature_flag
from risk_dashboard.platform.feature_flags.service import FeatureFlagService

_flags = FeatureFlagService()


class KillSwitchActiveError(Exception):
    """Raised when an operation is attempted while the kill switch is active."""

    def __init__(self, message: str = "Agentic execution is disabled via kill switch.", status_code: int = 503) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def is_kill_switch_active() -> bool:
    """Check if emergency kill switch is tripped or agentic feature flag is disabled."""
    # Emergency env-based hard kill switch
    if os.environ.get("AGENTIC_KILL_SWITCH", "").lower() in ("true", "1", "yes", "enabled"):
        return True

    # Feature flag check
    enabled = _flags.is_enabled("agentic.enabled", default=True)
    return not enabled


def assert_agentic_available() -> None:
    """Validate system availability, raising KillSwitchActiveError if disabled."""
    if is_kill_switch_active():
        raise KillSwitchActiveError("Agentic execution is disabled via kill switch.", status_code=503)
