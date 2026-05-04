from __future__ import annotations

from dataclasses import dataclass, field

from fastapi import APIRouter


@dataclass(frozen=True)
class ModuleDefinition:
    id: str
    slug: str
    enabled_by_default: bool = True
    dependencies: tuple[str, ...] = ()
    feature_flags: tuple[str, ...] = ()
    permission_scopes: tuple[str, ...] = ()
    public_router: APIRouter | None = None
    public_mount_prefix: str = ""
    pro_router: APIRouter | None = None
    pro_mount_prefix: str = "/api/v1/pro"
    admin_router: APIRouter | None = None
    admin_mount_prefix: str = "/admin"
    startup_hooks: tuple[str, ...] = ()
    job_handlers: tuple[str, ...] = field(default_factory=tuple)
