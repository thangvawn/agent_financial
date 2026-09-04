from __future__ import annotations

from typing import Any


def rank_candidates(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Deterministic ranking for Home Journey candidates.

    Sort order:
    1. priority DESC
    2. updated_at DESC (continuity/freshness)
    3. created_at DESC
    4. candidate_id ASC (stable tie-breaker across shuffles)

    Returns exactly 1 candidate dict or None if candidates list is empty.
    """
    if not candidates:
        return None

    def sort_key(c: dict[str, Any]) -> tuple[int, str, str, str]:
        # Negative priority for DESC sort
        p = -int(c.get("priority", 0))
        # Negative string for DESC sort can use reverse=True or invert logic.
        # To keep tuple comparison clean, we sort with a key function:
        return (
            p,
            c.get("updated_at", ""),
            c.get("created_at", ""),
            c.get("candidate_id", ""),
        )

    # We sort by:
    # priority DESC (higher first)
    # updated_at DESC (newer first)
    # created_at DESC (newer first)
    # candidate_id ASC (lexicographical tie-breaker)
    sorted_candidates = sorted(
        candidates,
        key=lambda c: (
            -int(c.get("priority", 0)),
            # To sort string timestamps DESC, we can negate unix timestamp or reverse sort
            # For ISO strings, comparing negative timestamp:
            c.get("candidate_id", ""),
        ),
    )

    # Let's do a strict multi-tier deterministic sort:
    def rank_tuple(c: dict[str, Any]) -> tuple[int, str, str, str]:
        priority = int(c.get("priority", 0))
        updated_at = str(c.get("updated_at", ""))
        created_at = str(c.get("created_at", ""))
        cid = str(c.get("candidate_id", ""))
        return (priority, updated_at, created_at, cid)

    # For priority DESC, updated_at DESC, created_at DESC, cid ASC:
    # Custom comparator or standard sorting:
    candidates_copy = list(candidates)

    # Secondary sort by candidate_id ASC first
    candidates_copy.sort(key=lambda c: str(c.get("candidate_id", "")))
    # Then by created_at DESC
    candidates_copy.sort(key=lambda c: str(c.get("created_at", "")), reverse=True)
    # Then by updated_at DESC
    candidates_copy.sort(key=lambda c: str(c.get("updated_at", "")), reverse=True)
    # Finally by priority DESC (Python sort is stable!)
    candidates_copy.sort(key=lambda c: int(c.get("priority", 0)), reverse=True)

    return candidates_copy[0]

