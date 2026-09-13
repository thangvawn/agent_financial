from __future__ import annotations

from typing import Literal

TierType = Literal["free", "community", "starter", "pro", "enterprise"]
RoleType = Literal["user", "admin", "operator"]

BASE_SCOPES: tuple[str, ...] = (
    "account:market_portfolio:read",
    "me:home_journey:read",
    "me:home_journey:feedback",
    "me:preferences:read",
    "me:preferences:write",
    "me:memory:read",
    "me:memory:delete",
    "me:data:export",
    "agentic:read",
    "financials:read",
    "bctc:report:read",
    "bctc:formula:read",
    "bctc:evidence:read",
)

STARTER_SCOPES: tuple[str, ...] = BASE_SCOPES + (
    "account:market_portfolio:write",
    "agentic:write",
)

PRO_SCOPES: tuple[str, ...] = STARTER_SCOPES + (
    "pro:pro_lab:use",
    "pro:simulation:run",
    "agentic:advanced:execute",
)

ENTERPRISE_SCOPES: tuple[str, ...] = PRO_SCOPES + (
    "admin:pro_lab:manage",
    "admin:audit:read",
    "admin:break_glass:use",
)


def resolve_scopes(tier: str = "community", role: str = "user") -> tuple[str, ...]:
    """Dynamically resolve scopes based on user tier and role."""
    normalized_tier = tier.lower().strip()
    normalized_role = role.lower().strip()

    if normalized_role == "admin":
        return ENTERPRISE_SCOPES

    if normalized_tier in ("pro", "diamond", "golden"):
        return PRO_SCOPES
    if normalized_tier in ("starter", "silver", "bronze"):
        return STARTER_SCOPES
    if normalized_tier == "enterprise":
        return ENTERPRISE_SCOPES

    return BASE_SCOPES

