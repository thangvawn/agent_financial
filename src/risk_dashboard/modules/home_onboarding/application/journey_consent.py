from __future__ import annotations

from typing import Any


def resolve_home_consent(principal: Any) -> tuple[bool, bool]:
    """Resolve (personalization_consented, memory_consented) from principal.

    Invariant:
    If consent is missing, revoked, or memory is False without explicit
    home_personalization purpose, return (False, False).
    """
    if principal is None:
        return (False, False)

    consent = getattr(principal, "consent", None)
    if consent is None:
        return (False, False)

    # If consent has memory=True, memory consent implies personalization
    memory = bool(getattr(consent, "memory", False))
    personalization = memory

    # Check for custom purpose attribute or dictionary if present
    purposes = getattr(consent, "purposes", None)
    if isinstance(purposes, (list, tuple, set)) and "home_personalization" in purposes:
        personalization = True

    return (personalization, memory)

