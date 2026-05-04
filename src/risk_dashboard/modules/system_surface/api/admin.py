from __future__ import annotations

import pandas as pd
from fastapi import APIRouter

from risk_dashboard.platform.runtime.panel_store import set_panel_from_frame

router = APIRouter(tags=["Admin"])


@router.post("/load-panel", tags=["Admin"])
def load_panel(payload: dict) -> dict[str, str]:
    panel = pd.DataFrame(payload["records"])
    set_panel_from_frame(panel, source="admin/load-panel")
    return {"ok": "true", "rows": str(len(panel))}
