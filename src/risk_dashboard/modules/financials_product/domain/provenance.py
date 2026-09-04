from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from typing import Sequence


def derive_revision_id(source: str, fetched_at: str, periods: Sequence[str]) -> str:
    """Deterministic revision from source + time + period set."""
    sorted_periods = sorted(set(periods))
    canonical = f"{source}|{fetched_at}|{'|'.join(sorted_periods)}"
    return f"rev_{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:16]}"


def calculate_freshness_days(fetched_at_iso: str, now: datetime | None = None) -> int:
    """Calculate the age in days of a fetched dataset."""
    current_time = now or datetime.now(timezone.utc)
    try:
        cleaned_iso = fetched_at_iso.replace("Z", "+00:00")
        fetched_dt = datetime.fromisoformat(cleaned_iso)
        if fetched_dt.tzinfo is None:
            fetched_dt = fetched_dt.replace(tzinfo=timezone.utc)
        delta = current_time - fetched_dt
        return max(0, delta.days)
    except Exception:
        return 0


def is_fresh(fetched_at_iso: str, max_days: int = 90, now: datetime | None = None) -> bool:
    """Determine whether the data satisfies freshness policy."""
    return calculate_freshness_days(fetched_at_iso, now=now) <= max_days

