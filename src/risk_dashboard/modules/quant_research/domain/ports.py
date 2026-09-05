"""Domain interfaces and protocols for quant_research."""
from __future__ import annotations

from datetime import date
from typing import Literal, Protocol

from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.quant_research.schemas.artifacts import QuantResearchArtifactV1
from risk_dashboard.modules.quant_research.schemas.requests import QuantResearchRequestV1
from risk_dashboard.modules.quant_research.schemas.tools import QuantToolResultV1


class QuantEnginePort(Protocol):
    """Port for canonical quant engine operations."""

    async def run_eod_analysis(
        self, *, as_of: date, run_id: str | None = None
    ) -> QuantToolResultV1: ...

    async def compare_macro_scenario(
        self,
        *,
        as_of: date,
        usd_vnd_rate: float | None = None,
        sbv_interest_rate_pct: float | None = None,
    ) -> QuantToolResultV1: ...

    async def get_model_research_report(
        self, *, model_ref: Literal["latest"] = "latest"
    ) -> QuantToolResultV1: ...


class QuantReviewerPort(Protocol):
    """Port for deterministic numeric review."""

    def review(
        self,
        *,
        candidate: QuantResearchArtifactV1,
        tool_result: QuantToolResultV1,
    ) -> QuantResearchArtifactV1: ...


class QuantResearchServicePort(Protocol):
    """Port for the main quant research orchestration service."""

    async def execute_research(
        self, *, request: QuantResearchRequestV1, principal: AuthPrincipal
    ) -> QuantResearchArtifactV1: ...

