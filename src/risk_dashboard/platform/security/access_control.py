from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from fastapi import Header, HTTPException

from risk_dashboard.platform.database import open_app_state_db


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class AccessRoleAssignment:
    actor_id: str
    role: str
    scopes: tuple[str, ...]
    status: str = "active"
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class AccessToken:
    token_id: str
    actor_id: str
    role: str
    scopes: tuple[str, ...]
    status: str = "active"
    created_at: str = field(default_factory=utc_now_iso)
    expires_at: str | None = None


ROLE_SCOPES: dict[str, tuple[str, ...]] = {
    "public_user": ("public:*",),
    "pro_lab_user": ("public:pro_lab:read", "pro:pro_lab:use"),
    "internal_admin": ("public:*", "pro:*", "admin:pro_lab:manage"),
}


class SqliteAccessControlRepository:
    def save_role_assignment(self, assignment: AccessRoleAssignment) -> AccessRoleAssignment:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO access_role_assignments (actor_id, role, scopes_json, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(actor_id, role) DO UPDATE SET
                  scopes_json = excluded.scopes_json,
                  status = excluded.status,
                  updated_at = excluded.updated_at
                """,
                (
                    assignment.actor_id,
                    assignment.role,
                    json.dumps(list(assignment.scopes), ensure_ascii=False),
                    assignment.status,
                    assignment.created_at,
                    assignment.updated_at,
                ),
            )
            conn.commit()
        return assignment

    def list_roles(self, *, actor_id: str) -> list[AccessRoleAssignment]:
        with open_app_state_db() as conn:
            rows = conn.execute(
                """
                SELECT actor_id, role, scopes_json, status, created_at, updated_at
                FROM access_role_assignments
                WHERE actor_id = ? AND status = 'active'
                ORDER BY created_at ASC
                """,
                (actor_id,),
            ).fetchall()
        return [
            AccessRoleAssignment(
                actor_id=row["actor_id"],
                role=row["role"],
                scopes=tuple(json.loads(row["scopes_json"] or "[]")),
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def save_token(self, token: AccessToken) -> AccessToken:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO access_tokens (token_id, actor_id, role, scopes_json, status, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(token_id) DO UPDATE SET
                  status = excluded.status,
                  expires_at = excluded.expires_at
                """,
                (
                    token.token_id,
                    token.actor_id,
                    token.role,
                    json.dumps(list(token.scopes), ensure_ascii=False),
                    token.status,
                    token.created_at,
                    token.expires_at,
                ),
            )
            conn.commit()
        return token

    def get_token(self, *, token_id: str) -> AccessToken | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT token_id, actor_id, role, scopes_json, status, created_at, expires_at
                FROM access_tokens
                WHERE token_id = ?
                """,
                (token_id,),
            ).fetchone()
        if row is None:
            return None
        return AccessToken(
            token_id=row["token_id"],
            actor_id=row["actor_id"],
            role=row["role"],
            scopes=tuple(json.loads(row["scopes_json"] or "[]")),
            status=row["status"],
            created_at=row["created_at"],
            expires_at=row["expires_at"],
        )

    def list_tokens(self, *, actor_id: str) -> list[AccessToken]:
        with open_app_state_db() as conn:
            rows = conn.execute(
                """
                SELECT token_id, actor_id, role, scopes_json, status, created_at, expires_at
                FROM access_tokens
                WHERE actor_id = ?
                ORDER BY created_at DESC
                """,
                (actor_id,),
            ).fetchall()
        return [
            AccessToken(
                token_id=row["token_id"],
                actor_id=row["actor_id"],
                role=row["role"],
                scopes=tuple(json.loads(row["scopes_json"] or "[]")),
                status=row["status"],
                created_at=row["created_at"],
                expires_at=row["expires_at"],
            )
            for row in rows
        ]

    def revoke_token(self, *, token_id: str) -> AccessToken | None:
        with open_app_state_db() as conn:
            conn.execute(
                "UPDATE access_tokens SET status = 'revoked' WHERE token_id = ?",
                (token_id,),
            )
            conn.commit()
        return self.get_token(token_id=token_id)


def assign_role(*, actor_id: str, role: str, repo: SqliteAccessControlRepository | None = None) -> AccessRoleAssignment:
    selected_repo = repo or SqliteAccessControlRepository()
    scopes = ROLE_SCOPES.get(role)
    if not scopes:
        raise ValueError(f"Unknown access role: {role}")
    assignment = AccessRoleAssignment(actor_id=actor_id, role=role, scopes=scopes)
    return selected_repo.save_role_assignment(assignment)


def issue_token_for_actor(
    *,
    actor_id: str,
    role: str,
    ttl_hours: int = 12,
    repo: SqliteAccessControlRepository | None = None,
) -> AccessToken:
    selected_repo = repo or SqliteAccessControlRepository()
    roles = selected_repo.list_roles(actor_id=actor_id)
    matched = next((item for item in roles if item.role == role), None)
    if matched is None:
        raise ValueError("Actor chưa có role phù hợp để cấp token.")
    token = AccessToken(
        token_id=f"act_{uuid.uuid4().hex}",
        actor_id=actor_id,
        role=role,
        scopes=matched.scopes,
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=ttl_hours)).isoformat(),
    )
    return selected_repo.save_token(token)


def get_token_scopes(token_id: str, repo: SqliteAccessControlRepository | None = None) -> AccessToken | None:
    selected_repo = repo or SqliteAccessControlRepository()
    token = selected_repo.get_token(token_id=token_id)
    if token is None or token.status != "active":
        return None
    if token.expires_at:
        expires_at = datetime.fromisoformat(token.expires_at.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) >= expires_at:
            return None
    return token


def scope_allows(granted: tuple[str, ...], required: str) -> bool:
    if required in granted:
        return True
    required_prefix = required.split(":")[0]
    for scope in granted:
        if scope == "*":
            return True
        if scope.endswith(":*") and required.startswith(scope[:-1]):
            return True
        if scope == f"{required_prefix}:*":
            return True
    return False


def require_scope_from_token(
    required_scope: str,
    x_access_token: str | None = Header(default=None, alias="X-Access-Token"),
) -> AccessToken:
    token = get_token_scopes(x_access_token or "")
    if token is None:
        raise HTTPException(status_code=401, detail="Thiếu hoặc sai X-Access-Token.")
    if not scope_allows(token.scopes, required_scope):
        raise HTTPException(status_code=403, detail=f"Token không đủ quyền cho scope {required_scope}.")
    return token
