from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from risk_dashboard.modules.internal_ops.domain.contracts import (
    EvidenceItem,
    InvestigationRequest,
    OpsActionRecommendation,
    OpsInvestigationReport,
    SCHEMA_VERSION_V1,
    _validate_schema_major_1,
)


class StrictApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class InvestigationCreateApiRequest(InvestigationRequest):
    pass


class InvestigationApiResponse(StrictApiModel):
    schema_version: str = SCHEMA_VERSION_V1
    report: OpsInvestigationReport


class EvidenceListApiResponse(StrictApiModel):
    schema_version: str = SCHEMA_VERSION_V1
    investigation_id: str
    items: list[EvidenceItem]
    total: int = Field(ge=0)
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class RecommendationsApiResponse(StrictApiModel):
    schema_version: str = SCHEMA_VERSION_V1
    investigation_id: str
    items: list[OpsActionRecommendation]


class InvestigationStatusApiResponse(StrictApiModel):
    schema_version: str = SCHEMA_VERSION_V1
    investigation_id: str
    status: str
    created_at: str
    updated_at: str

