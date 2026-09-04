from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SourceLicense = Literal["open", "attribution_required", "licensed", "restricted"]
QualityFlag = Literal["ok", "degraded", "unreliable"]
SourceHealthStatus = Literal["healthy", "degraded", "unreliable", "unavailable"]


@dataclass(frozen=True)
class SourceHealthRecord:
    source_id: str
    name: str
    tier: int
    region: str
    category: str
    license_class: SourceLicense
    attribution_text: str | None = None
    is_available: bool = True
    last_success_at: str | None = None
    staleness_minutes: int = 0
    error_rate_24h: float = 0.0
    quality_flag: QualityFlag = "ok"
    redistribution_allowed: bool = True

