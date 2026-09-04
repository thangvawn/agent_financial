from __future__ import annotations

from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal


def has_scope(principal: AuthPrincipal, required: str) -> bool:
    return required in principal.scopes


def check_ownership(principal: AuthPrincipal, resource_account_id: str) -> bool:
    return principal.account_id == resource_account_id
