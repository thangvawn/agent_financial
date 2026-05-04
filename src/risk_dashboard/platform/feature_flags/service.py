from __future__ import annotations

import os


class FeatureFlagService:
    def is_enabled(self, flag_name: str, *, default: bool = False) -> bool:
        env_name = "RISK_FLAG__" + flag_name.upper().replace(".", "__")
        raw = os.getenv(env_name)
        if raw is None:
            return default
        return raw.strip().lower() in {"1", "true", "yes", "on"}
