"""Timezone-safe parsing for timestamps persisted by News Intelligence."""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


def parse_utc_datetime(value: object) -> datetime | None:
    """Parse ISO/RFC-2822 input into an aware UTC datetime.

    Older rows and third-party producers may omit an offset.  We interpret
    those values as UTC because all new News timestamps are written in UTC;
    callers can still treat malformed values as unavailable instead of
    crashing a feed request.
    """

    if isinstance(value, datetime):
        parsed = value
    else:
        raw = str(value or "").strip()
        if not raw:
            return None
        if raw.endswith("Z"):
            raw = f"{raw[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(raw)
        except (TypeError, ValueError):
            try:
                parsed = parsedate_to_datetime(raw)
            except (TypeError, ValueError, OverflowError):
                return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    try:
        return parsed.astimezone(timezone.utc)
    except (OverflowError, ValueError):
        return None
