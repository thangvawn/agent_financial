from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from risk_dashboard.modules.agentic_core.application.memory_service import MemoryService
from risk_dashboard.modules.auth.application.dependencies import resolve_principal
from risk_dashboard.modules.auth.infrastructure.sqlite import SqliteAccountConsentRepository
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal, ConsentSnapshot

router = APIRouter(tags=["User Rights & Privacy"])


class PreferencesUpdateRequest(BaseModel):
    memory: bool | None = None
    analytics: bool | None = None
    policy_version: str = "1.0.0"


def _consents() -> SqliteAccountConsentRepository:
    return SqliteAccountConsentRepository()


def _memory_service() -> MemoryService:
    return MemoryService()


@router.get("/agent-preferences")
def get_preferences(principal: AuthPrincipal = Depends(resolve_principal)) -> dict[str, Any]:
    consent = _consents().get(account_id=principal.account_id)
    if consent is None:
        return {
            "account_id": principal.account_id,
            "memory": False,
            "memory_mode": "off",
            "analytics": False,
            "analytics_opt_in": False,
            "policy_version": "1.0.0",
        }
    return {
        "account_id": principal.account_id,
        "memory": consent.memory,
        "memory_mode": "on" if consent.memory else "off",
        "analytics": consent.analytics,
        "analytics_opt_in": consent.analytics,
        "policy_version": consent.policy_version,
        "consented_at": consent.consented_at,
    }


@router.patch("/agent-preferences")
def update_preferences(
    req: PreferencesUpdateRequest,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, Any]:
    current = _consents().get(account_id=principal.account_id)
    now_iso = datetime.now(timezone.utc).isoformat()
    new_memory = req.memory if req.memory is not None else (current.memory if current else False)
    new_analytics = req.analytics if req.analytics is not None else (current.analytics if current else False)

    snapshot = ConsentSnapshot(
        memory=new_memory,
        analytics=new_analytics,
        policy_version=req.policy_version,
        consented_at=now_iso,
    )
    _consents().save(account_id=principal.account_id, consent=snapshot)
    return {
        "account_id": principal.account_id,
        "memory": snapshot.memory,
        "memory_mode": "on" if snapshot.memory else "off",
        "analytics": snapshot.analytics,
        "analytics_opt_in": snapshot.analytics,
        "policy_version": snapshot.policy_version,
        "consented_at": snapshot.consented_at,
    }


@router.get("/agent-memory")
def list_user_memories(principal: AuthPrincipal = Depends(resolve_principal)) -> dict[str, Any]:
    items = _memory_service().list_memories(account_id=principal.account_id)
    return {
        "account_id": principal.account_id,
        "total": len(items),
        "items": [item.model_dump(mode="json") for item in items],
    }


@router.delete("/agent-memory/{memory_id}")
def delete_single_memory(
    memory_id: str,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, Any]:
    mem = _memory_service().get_memory(account_id=principal.account_id, memory_id=memory_id)
    if mem is None:
        raise HTTPException(status_code=404, detail="Memory not found or unauthorized")
    _memory_service().forget_memory(account_id=principal.account_id, memory_id=memory_id)
    return {"status": "ok", "deleted_memory_id": memory_id}


@router.delete("/agent-memory")
def delete_all_user_memories(
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, Any]:
    deleted_count = _memory_service().purge_account(account_id=principal.account_id)
    return {"status": "ok", "deleted_count": deleted_count}


@router.post("/agent-data-export")
def export_user_agent_data(
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, Any]:
    preferences = get_preferences(principal)
    memories = _memory_service().export_memories(account_id=principal.account_id)
    now_iso = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": "1.0.0",
        "account_id": principal.account_id,
        "exported_at": now_iso,
        "export_timestamp": now_iso,
        "preferences": preferences,
        "memories": memories.get("memories", []),
        "data": {
            "preferences": preferences,
            "memories": memories.get("memories", []),
        },
    }

