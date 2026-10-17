from __future__ import annotations

import hmac
import os

import pandas as pd
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from risk_dashboard.platform.runtime.panel_store import PanelValidationError, set_panel_from_frame

router = APIRouter(tags=["Admin"])


class PanelLoadRequest(BaseModel):
    records: list[dict[str, object]] = Field(min_length=1, max_length=1_000_000)


def verify_panel_admin(
    x_admin_system_key: str | None = Header(default=None, alias="X-Admin-System-Key"),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> bool:
    """Protect the global in-memory panel mutation endpoint.

    The API-key middleware protects this route when ``API_SECRET_KEY`` is set.
    The dedicated header also makes the endpoint safe in local deployments that
    intentionally leave the global API key disabled.
    """
    expected = os.getenv("ADMIN_SYSTEM_KEY", "").strip() or os.getenv("API_SECRET_KEY", "").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Panel admin API chưa bật: đặt ADMIN_SYSTEM_KEY hoặc API_SECRET_KEY trong .env.",
        )
    supplied = (x_admin_system_key or x_api_key or "").strip()
    if not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Thiếu hoặc sai khóa quản trị panel.")
    return True


@router.post("/load-panel", tags=["Admin"])
def load_panel(
    payload: PanelLoadRequest, _: bool = Depends(verify_panel_admin)
) -> dict[str, object]:
    panel = pd.DataFrame(payload.records)
    try:
        set_panel_from_frame(panel, source="admin/load-panel")
    except PanelValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"ok": True, "rows": len(panel), "source_kind": "admin_upload"}
