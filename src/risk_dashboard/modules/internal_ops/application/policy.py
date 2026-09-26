from __future__ import annotations

from datetime import datetime, timezone, timedelta
from risk_dashboard.compat import StrEnum
from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict, Field

from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.internal_ops.domain.contracts import (
    FORBIDDEN_TOOL_NAMES,
    SCHEMA_VERSION_V1,
)


class OpsRole(StrEnum):
    SUPPORT_VIEWER = "support_viewer"
    CONTENT_OPERATOR = "content_operator"
    RELIABILITY_OPERATOR = "reliability_operator"
    TRUST_REVIEWER = "trust_reviewer"
    SECURITY_ADMIN = "security_admin"


ROLE_ALLOWED_MODULES: dict[OpsRole, tuple[str, ...]] = {
    OpsRole.SUPPORT_VIEWER: ("analytics_monitoring",),
    OpsRole.CONTENT_OPERATOR: ("analytics_monitoring", "admin_cms"),
    OpsRole.RELIABILITY_OPERATOR: ("analytics_monitoring", "agentic_core"),
    OpsRole.TRUST_REVIEWER: ("analytics_monitoring", "trust_safety"),
    OpsRole.SECURITY_ADMIN: (
        "analytics_monitoring",
        "trust_safety",
        "admin_cms",
        "agentic_core",
    ),
}

ROLE_SCOPES: dict[str, OpsRole] = {
    "admin:internal_ops:security_admin": OpsRole.SECURITY_ADMIN,
    "admin:internal_ops:trust_reviewer": OpsRole.TRUST_REVIEWER,
    "admin:internal_ops:reliability_operator": OpsRole.RELIABILITY_OPERATOR,
    "admin:internal_ops:content_operator": OpsRole.CONTENT_OPERATOR,
    "admin:internal_ops:support_viewer": OpsRole.SUPPORT_VIEWER,
}


class PolicyDeniedError(Exception):
    pass


class InvalidPurposeError(PolicyDeniedError):
    pass


class GrantExpiredError(PolicyDeniedError):
    pass


class PurposeGrant(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = SCHEMA_VERSION_V1
    grant_id: str
    account_id: str
    role: OpsRole
    purpose: str
    allowed_modules: tuple[str, ...]
    expires_at: str
    resource_scope: str | None = None
    is_breakglass: bool = False
    breakglass_reason: str | None = None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_iso(dt_str: str) -> datetime:
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))


class PolicyEngine:
    @staticmethod
    def resolve_role(principal: AuthPrincipal) -> OpsRole:
        for scope, role in ROLE_SCOPES.items():
            if scope in principal.scopes:
                return role
        # Check granular scopes
        if "admin:internal_ops:trust_read" in principal.scopes:
            return OpsRole.TRUST_REVIEWER
        if "admin:internal_ops:content_read" in principal.scopes:
            return OpsRole.CONTENT_OPERATOR
        if "admin:internal_ops:report_read" in principal.scopes:
            return OpsRole.SUPPORT_VIEWER
        if "admin:internal_ops:investigate" in principal.scopes:
            return OpsRole.SUPPORT_VIEWER
        raise PolicyDeniedError(f"Principal {principal.account_id} lacks internal_ops roles or scopes")

    @classmethod
    def create_grant(
        cls,
        principal: AuthPrincipal,
        purpose: str,
        requested_modules: tuple[str, ...] | None = None,
        ttl_seconds: int = 3600,
        resource_scope: str | None = None,
        breakglass: bool = False,
        breakglass_reason: str | None = None,
    ) -> PurposeGrant:
        if not purpose or len(purpose.strip()) < 8:
            raise InvalidPurposeError("Purpose string must be at least 8 characters.")

        role = cls.resolve_role(principal)
        now = utc_now()

        if breakglass:
            if role != OpsRole.SECURITY_ADMIN:
                raise PolicyDeniedError("Break-glass grants require security_admin role.")
            if not breakglass_reason or len(breakglass_reason.strip()) < 8:
                raise InvalidPurposeError("Break-glass requires a reason of at least 8 characters.")
            effective_ttl = min(ttl_seconds, 900)  # Max 15 minutes
        else:
            effective_ttl = min(max(ttl_seconds, 60), 14400)

        expires_at = (now + timedelta(seconds=effective_ttl)).isoformat()
        role_modules = ROLE_ALLOWED_MODULES[role]

        if requested_modules:
            for mod in requested_modules:
                if mod not in role_modules:
                    raise PolicyDeniedError(f"Role {role} is not authorized for module '{mod}'")
            allowed = tuple(mod for mod in requested_modules if mod in role_modules)
        else:
            allowed = role_modules

        return PurposeGrant(
            grant_id=f"grant-{uuid.uuid4().hex[:12]}",
            account_id=principal.account_id,
            role=role,
            purpose=purpose.strip(),
            allowed_modules=allowed,
            expires_at=expires_at,
            resource_scope=resource_scope,
            is_breakglass=breakglass,
            breakglass_reason=breakglass_reason.strip() if breakglass_reason else None,
        )

    @staticmethod
    def is_grant_valid(grant: PurposeGrant) -> bool:
        return parse_iso(grant.expires_at) > utc_now()

    @classmethod
    def authorize_tool_call(
        cls,
        grant: PurposeGrant,
        tool_id: str,
        source_module: str | None = None,
    ) -> bool:
        if not cls.is_grant_valid(grant):
            raise GrantExpiredError(f"Grant {grant.grant_id} has expired.")

        # Hard invariant: forbidden tools are NEVER authorized under any role or breakglass
        if tool_id in FORBIDDEN_TOOL_NAMES:
            raise PolicyDeniedError(f"Tool '{tool_id}' is strictly forbidden and cannot be authorized.")

        if source_module and source_module not in grant.allowed_modules:
            raise PolicyDeniedError(
                f"Grant role {grant.role} does not permit access to module '{source_module}'."
            )
        return True
