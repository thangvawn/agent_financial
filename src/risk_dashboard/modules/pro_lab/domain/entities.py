from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ProLabBlueprint:
    blueprint_id: str
    user_id: str
    name: str
    objective: str
    asset_universe: tuple[str, ...]
    benchmark: str
    rebalance_frequency: str
    risk_constraints: str
    assumptions_note: str | None
    status: str = "draft"
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class ProLabExperiment:
    experiment_id: str
    user_id: str
    blueprint_id: str | None
    experiment_type: str
    status: str
    input_payload: dict[str, object]
    output_payload: dict[str, object]
    created_at: str = field(default_factory=utc_now_iso)
    review_status: str = "pending_review"
    review_notes: str | None = None
    reviewed_at: str | None = None
    reviewer_id: str | None = None


@dataclass(frozen=True)
class ProLabAuditLog:
    audit_id: str
    actor_id: str
    surface: str
    action: str
    target_type: str
    target_id: str | None
    metadata: dict[str, object]
    created_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class ProLabExperimentRun:
    run_id: str
    user_id: str
    experiment_id: str | None
    blueprint_id: str | None
    provider_id: str
    command_id: str
    status: str
    input_payload: dict[str, object]
    output_payload: dict[str, object]
    logs: tuple[dict[str, object], ...]
    progress_pct: int
    safety_flags: tuple[str, ...]
    data_freshness: dict[str, object]
    created_at: str = field(default_factory=utc_now_iso)
    completed_at: str | None = None


@dataclass(frozen=True)
class ProLabWorkspaceState:
    workspace_id: str
    user_id: str
    active_page: str
    open_panels: tuple[str, ...]
    selected_blueprint_id: str | None
    selected_experiment_id: str | None
    layout: dict[str, object]
    notes: str | None
    version: int = 1
    updated_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class SimulationExperimentSpec:
    spec_id: str
    account_id: str
    manifest_json: str
    status: str = "active"
    schema_version: str = "1.0.0"
    created_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class SimulationActionProposalEntity:
    proposal_id: str
    account_id: str
    run_id: str
    manifest_json: str
    status: str
    confirmation_token: str
    idempotency_key: str | None
    expires_at: str
    created_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class SimulationActionReceiptEntity:
    receipt_id: str
    proposal_id: str
    account_id: str
    status: str
    run_artifact_id: str | None
    error_code: str | None
    executed_at: str = field(default_factory=utc_now_iso)

