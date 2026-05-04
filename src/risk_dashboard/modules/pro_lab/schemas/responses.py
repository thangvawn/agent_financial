from __future__ import annotations

from pydantic import BaseModel


class ProLabTeaserResponse(BaseModel):
    enabled: bool
    pro_eligible: bool
    access_mode: str
    positioning: str
    public_boundary: list[str]
    pro_capabilities: list[str]
    admin_capabilities: list[str]


class ProLabBlueprintResponse(BaseModel):
    blueprint_id: str
    name: str
    objective: str
    asset_universe: list[str]
    benchmark: str
    rebalance_frequency: str
    risk_constraints: str
    assumptions_note: str | None = None
    status: str
    created_at: str
    updated_at: str


class ProLabExperimentResponse(BaseModel):
    experiment_id: str
    blueprint_id: str | None = None
    experiment_type: str
    status: str
    created_at: str
    review_status: str = "pending_review"
    review_notes: str | None = None
    reviewed_at: str | None = None
    reviewer_id: str | None = None
    notebook_sections: list[dict[str, object]]
    caveats: list[str]


class ProLabAuditResponse(BaseModel):
    audit_id: str
    actor_id: str
    surface: str
    action: str
    target_type: str
    target_id: str | None = None
    metadata: dict[str, object]
    created_at: str


class ProLabWorkspaceResponse(BaseModel):
    enabled: bool
    access_mode: str
    workspace_title: str
    workspace_summary: str
    blueprints: list[ProLabBlueprintResponse]
    experiments: list[ProLabExperimentResponse]
    capability_cards: list[dict[str, str]]


class ProLabBlueprintCompareResponse(BaseModel):
    left_blueprint_id: str
    right_blueprint_id: str
    summary: str
    differences: list[dict[str, str]]


class ProLabReportExportResponse(BaseModel):
    export_id: str
    filename: str
    content_type: str
    content: str
    confidence_label: str = "moderate_confidence"
    disclaimer_title: str | None = None
    disclaimer_text: str | None = None
    risk_banner: str | None = None
    what_this_is: str = ""
    what_this_is_not: str = ""
    generated_at: str


class ProLabAccessTokenResponse(BaseModel):
    actor_id: str
    role: str
    access_token: str
    scopes: list[str]
    expires_at: str | None = None


class ProLabSessionResponse(BaseModel):
    token_id: str
    actor_id: str
    role: str
    status: str
    scopes: list[str]
    created_at: str
    expires_at: str | None = None
    is_current: bool = False


class ProLabSessionListResponse(BaseModel):
    actor_id: str
    current_token_id: str | None = None
    sessions: list[ProLabSessionResponse]


class ProLabCommandResponse(BaseModel):
    command_id: str
    label: str
    description: str
    input_schema: dict[str, object]
    output_schema: dict[str, object]
    risk_level: str
    async_supported: bool
    requires_review: bool
    public_allowed: bool
    private_only: bool


class ProLabProviderResponse(BaseModel):
    provider_id: str
    label: str
    category: str
    description: str
    enabled: bool
    guardrails: list[str]
    commands: list[ProLabCommandResponse]


class ProLabCatalogResponse(BaseModel):
    providers: list[ProLabProviderResponse]
    private_capabilities_visible: bool
    guardrail_summary: list[str]


class ProLabExperimentRunResponse(BaseModel):
    run_id: str
    user_id: str
    experiment_id: str | None = None
    blueprint_id: str | None = None
    provider_id: str
    command_id: str
    status: str
    input_payload: dict[str, object]
    output_payload: dict[str, object]
    logs: list[dict[str, object]]
    progress_pct: int
    safety_flags: list[str]
    data_freshness: dict[str, object]
    created_at: str
    completed_at: str | None = None


class ProLabWorkspaceStateResponse(BaseModel):
    workspace_id: str
    user_id: str
    active_page: str
    open_panels: list[str]
    selected_blueprint_id: str | None = None
    selected_experiment_id: str | None = None
    layout: dict[str, object]
    notes: str | None = None
    version: int
    updated_at: str
