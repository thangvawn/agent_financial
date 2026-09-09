from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
import functools
import inspect
import logging
from typing import Any, Callable

from risk_dashboard.platform.feature_flags.service import FeatureFlagService

logger = logging.getLogger(__name__)

_flag_service = FeatureFlagService()


class FlagRegistry:
    _entries: deque[dict[str, Any]] = deque(maxlen=256)

    @classmethod
    def record(cls, flag_name: str, enabled: bool, caller: str) -> None:
        cls._entries.append({
            "flag_name": flag_name,
            "enabled": enabled,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "caller": caller,
        })

    @classmethod
    def get_entries(cls) -> list[dict[str, Any]]:
        return list(cls._entries)

    @classmethod
    def clear(cls) -> None:
        cls._entries.clear()


def feature_flag(flag_name: str, *, default: bool = False, fallback: Any = None) -> Callable:
    """Decorator checking feature flag before executing sync or async function.

    If the flag is disabled, returns fallback (default None) and logs evaluation.
    Evaluates dynamically on each invocation (<= 30s refresh SLA).
    """
    def decorator(fn: Callable) -> Callable:
        caller_name = getattr(fn, "__qualname__", getattr(fn, "__name__", str(fn)))

        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                enabled = _flag_service.is_enabled(flag_name, default=default)
                FlagRegistry.record(flag_name, enabled, caller_name)
                if not enabled:
                    logger.info("Feature flag '%s' disabled for %s; returning fallback", flag_name, caller_name)
                    return fallback
                return await fn(*args, **kwargs)
            return async_wrapper

        @functools.wraps(fn)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            enabled = _flag_service.is_enabled(flag_name, default=default)
            FlagRegistry.record(flag_name, enabled, caller_name)
            if not enabled:
                logger.info("Feature flag '%s' disabled for %s; returning fallback", flag_name, caller_name)
                return fallback
            return fn(*args, **kwargs)
        return sync_wrapper

    return decorator
