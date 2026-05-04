from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from risk_dashboard.modules.ai_assistant.application.services import RespondWithAssistant
from risk_dashboard.modules.ai_assistant.infrastructure.repositories.sqlite import SqliteAssistantConversationRepository
from risk_dashboard.modules.ai_assistant.schemas.requests import AssistantRespondRequest
from risk_dashboard.modules.ai_assistant.schemas.responses import AssistantRespondResponse
from risk_dashboard.modules.pro_lab.application.services import (
    ArchiveStrategyBlueprint,
    CompareStrategyBlueprints,
    ExportExperimentReport,
    GetProLabCatalog,
    GetProLabRun,
    GetProLabWorkspace,
    GetProLabWorkspaceState,
    is_pro_lab_local_test_open,
    ListProLabSessions,
    RevokeProLabSession,
    RunProLabCommand,
    RunBacktestLab,
    RunScenarioLab,
    SaveProLabWorkspaceState,
    SaveStrategyBlueprint,
    UpdateStrategyBlueprint,
)
from risk_dashboard.modules.pro_lab.infrastructure.repositories.sqlite import (
    SqliteProLabAuditRepository,
    SqliteProLabBlueprintRepository,
    SqliteProLabExperimentRepository,
    SqliteProLabExperimentRunRepository,
    SqliteProLabWorkspaceStateRepository,
)
from risk_dashboard.modules.pro_lab.schemas.requests import (
    ProLabBacktestRunRequest,
    ProLabBlueprintCreateRequest,
    ProLabBlueprintUpdateRequest,
    ProLabCommandRunRequest,
    ProLabScenarioRunRequest,
    ProLabWorkspaceStateRequest,
)
from risk_dashboard.modules.pro_lab.schemas.responses import (
    ProLabBlueprintCompareResponse,
    ProLabBlueprintResponse,
    ProLabCatalogResponse,
    ProLabExperimentResponse,
    ProLabExperimentRunResponse,
    ProLabReportExportResponse,
    ProLabSessionListResponse,
    ProLabSessionResponse,
    ProLabWorkspaceStateResponse,
    ProLabWorkspaceResponse,
)
from risk_dashboard.platform.security.access_control import AccessToken, SqliteAccessControlRepository, require_scope_from_token

router = APIRouter(prefix="/pro-lab", tags=["Pro Lab"])


def _blueprints() -> SqliteProLabBlueprintRepository:
    return SqliteProLabBlueprintRepository()


def _experiments() -> SqliteProLabExperimentRepository:
    return SqliteProLabExperimentRepository()


def _audit() -> SqliteProLabAuditRepository:
    return SqliteProLabAuditRepository()


def _runs() -> SqliteProLabExperimentRunRepository:
    return SqliteProLabExperimentRunRepository()


def _workspaces() -> SqliteProLabWorkspaceStateRepository:
    return SqliteProLabWorkspaceStateRepository()


def _access_control() -> SqliteAccessControlRepository:
    return SqliteAccessControlRepository()


def _assistant() -> RespondWithAssistant:
    return RespondWithAssistant(conversations=SqliteAssistantConversationRepository())


def _require_pro_scope(
    x_access_token: str | None = Header(default=None, alias="X-Access-Token"),
) -> AccessToken:
    if is_pro_lab_local_test_open():
        return AccessToken(
            token_id=x_access_token or "local_pro_lab_bypass",
            actor_id="local_pro_lab_user",
            role="internal_admin",
            scopes=("public:*", "pro:*", "admin:pro_lab:manage"),
        )
    return require_scope_from_token("pro:pro_lab:use", x_access_token)


@router.get("/workspace", response_model=ProLabWorkspaceResponse)
def pro_lab_workspace(user_id: str, token: AccessToken = Depends(_require_pro_scope)) -> ProLabWorkspaceResponse:
    if token.actor_id != user_id and token.role != "internal_admin":
        raise HTTPException(status_code=403, detail="Token không được phép mở workspace của user khác.")
    return GetProLabWorkspace(blueprints=_blueprints(), experiments=_experiments()).execute(user_id=user_id)


@router.get("/catalog", response_model=ProLabCatalogResponse)
def pro_lab_catalog(token: AccessToken = Depends(_require_pro_scope)) -> ProLabCatalogResponse:
    return GetProLabCatalog().execute(include_private=token.role == "internal_admin" or is_pro_lab_local_test_open())


@router.get("/workspace-state", response_model=ProLabWorkspaceStateResponse)
def pro_lab_workspace_state(user_id: str, token: AccessToken = Depends(_require_pro_scope)) -> ProLabWorkspaceStateResponse:
    if token.actor_id != user_id and token.role != "internal_admin":
        raise HTTPException(status_code=403, detail="Token không được phép mở workspace state của user khác.")
    return GetProLabWorkspaceState(workspaces=_workspaces()).execute(user_id=user_id)


@router.put("/workspace-state", response_model=ProLabWorkspaceStateResponse)
def pro_lab_save_workspace_state(
    req: ProLabWorkspaceStateRequest,
    token: AccessToken = Depends(_require_pro_scope),
) -> ProLabWorkspaceStateResponse:
    if token.actor_id != req.user_id and token.role != "internal_admin":
        raise HTTPException(status_code=403, detail="Token không được phép lưu workspace state của user khác.")
    return SaveProLabWorkspaceState(workspaces=_workspaces(), audit=_audit()).execute(
        user_id=req.user_id,
        active_page=req.active_page,
        open_panels=req.open_panels,
        selected_blueprint_id=req.selected_blueprint_id,
        selected_experiment_id=req.selected_experiment_id,
        layout=req.layout,
        notes=req.notes,
    )


@router.get("/sessions", response_model=ProLabSessionListResponse)
def pro_lab_sessions(
    user_id: str,
    token: AccessToken = Depends(_require_pro_scope),
) -> ProLabSessionListResponse:
    if token.actor_id != user_id and token.role != "internal_admin":
        raise HTTPException(status_code=403, detail="Token không được phép xem sessions của user khác.")
    return ListProLabSessions(access_control=_access_control()).execute(
        actor_id=user_id,
        current_token_id=token.token_id if token.actor_id == user_id else None,
    )


@router.post("/sessions/{token_id}/revoke", response_model=ProLabSessionResponse)
def pro_lab_revoke_session(
    token_id: str,
    user_id: str,
    token: AccessToken = Depends(_require_pro_scope),
) -> ProLabSessionResponse:
    if token.actor_id != user_id and token.role != "internal_admin":
        raise HTTPException(status_code=403, detail="Token không được phép revoke sessions của user khác.")
    try:
        return RevokeProLabSession(access_control=_access_control(), audit=_audit()).execute(
            actor_id=user_id,
            token_id=token_id,
            revoked_by=token.actor_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/blueprints", response_model=ProLabBlueprintResponse)
def pro_lab_create_blueprint(
    req: ProLabBlueprintCreateRequest,
    token: AccessToken = Depends(_require_pro_scope),
) -> ProLabBlueprintResponse:
    if token.actor_id != req.user_id and token.role != "internal_admin":
        raise HTTPException(status_code=403, detail="Token không được phép tạo blueprint cho user khác.")
    return SaveStrategyBlueprint(blueprints=_blueprints(), audit=_audit()).execute(
        user_id=req.user_id,
        name=req.name,
        objective=req.objective,
        asset_universe=req.asset_universe,
        benchmark=req.benchmark,
        rebalance_frequency=req.rebalance_frequency,
        risk_constraints=req.risk_constraints,
        assumptions_note=req.assumptions_note,
    )


@router.patch("/blueprints/{blueprint_id}", response_model=ProLabBlueprintResponse)
def pro_lab_update_blueprint(
    blueprint_id: str,
    req: ProLabBlueprintUpdateRequest,
    token: AccessToken = Depends(_require_pro_scope),
) -> ProLabBlueprintResponse:
    if token.actor_id != req.user_id and token.role != "internal_admin":
        raise HTTPException(status_code=403, detail="Token không được phép sửa blueprint của user khác.")
    try:
        return UpdateStrategyBlueprint(blueprints=_blueprints(), audit=_audit()).execute(
            blueprint_id=blueprint_id,
            user_id=req.user_id,
            name=req.name,
            objective=req.objective,
            asset_universe=req.asset_universe,
            benchmark=req.benchmark,
            rebalance_frequency=req.rebalance_frequency,
            risk_constraints=req.risk_constraints,
            assumptions_note=req.assumptions_note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/blueprints/{blueprint_id}/archive", response_model=ProLabBlueprintResponse)
def pro_lab_archive_blueprint(
    blueprint_id: str,
    user_id: str = Query(..., min_length=8),
    token: AccessToken = Depends(_require_pro_scope),
) -> ProLabBlueprintResponse:
    if token.actor_id != user_id and token.role != "internal_admin":
        raise HTTPException(status_code=403, detail="Token không được phép archive blueprint của user khác.")
    try:
        return ArchiveStrategyBlueprint(blueprints=_blueprints(), audit=_audit()).execute(
            blueprint_id=blueprint_id,
            user_id=user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/blueprints/compare", response_model=ProLabBlueprintCompareResponse)
def pro_lab_compare_blueprints(
    user_id: str,
    left_id: str,
    right_id: str,
    token: AccessToken = Depends(_require_pro_scope),
) -> ProLabBlueprintCompareResponse:
    if token.actor_id != user_id and token.role != "internal_admin":
        raise HTTPException(status_code=403, detail="Token không được phép compare blueprint của user khác.")
    try:
        return CompareStrategyBlueprints(blueprints=_blueprints(), audit=_audit()).execute(
            user_id=user_id,
            left_id=left_id,
            right_id=right_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/scenario-lab/run", response_model=ProLabExperimentResponse)
def pro_lab_run_scenario(
    req: ProLabScenarioRunRequest,
    token: AccessToken = Depends(_require_pro_scope),
) -> ProLabExperimentResponse:
    if token.actor_id != req.user_id and token.role != "internal_admin":
        raise HTTPException(status_code=403, detail="Token không được phép chạy scenario cho user khác.")
    try:
        return RunScenarioLab(
            blueprints=_blueprints(),
            experiments=_experiments(),
            audit=_audit(),
        ).execute(
            user_id=req.user_id,
            blueprint_id=req.blueprint_id,
            scenario_preset=req.scenario_preset,
            usd_vnd_rate=req.usd_vnd_rate,
            sbv_interest_rate_pct=req.sbv_interest_rate_pct,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/backtest-lab/run", response_model=ProLabExperimentResponse)
def pro_lab_run_backtest(
    req: ProLabBacktestRunRequest,
    token: AccessToken = Depends(_require_pro_scope),
) -> ProLabExperimentResponse:
    if token.actor_id != req.user_id and token.role != "internal_admin":
        raise HTTPException(status_code=403, detail="Token không được phép chạy backtest cho user khác.")
    try:
        return RunBacktestLab(
            blueprints=_blueprints(),
            experiments=_experiments(),
            audit=_audit(),
        ).execute(
            user_id=req.user_id,
            blueprint_id=req.blueprint_id,
            start_date=req.start_date,
            end_date=req.end_date,
            initial_capital=req.initial_capital,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/runs", response_model=ProLabExperimentRunResponse)
def pro_lab_run_provider_command(
    req: ProLabCommandRunRequest,
    token: AccessToken = Depends(_require_pro_scope),
) -> ProLabExperimentRunResponse:
    if token.actor_id != req.user_id and token.role != "internal_admin":
        raise HTTPException(status_code=403, detail="Token không được phép chạy command cho user khác.")
    try:
        return RunProLabCommand(
            blueprints=_blueprints(),
            experiments=_experiments(),
            runs=_runs(),
            audit=_audit(),
        ).execute(
            user_id=req.user_id,
            provider_id=req.provider_id,
            command_id=req.command_id,
            blueprint_id=req.blueprint_id,
            input_payload=req.input_payload,
            include_private=token.role == "internal_admin" or is_pro_lab_local_test_open(),
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/runs/{run_id}", response_model=ProLabExperimentRunResponse)
def pro_lab_get_run(
    run_id: str,
    user_id: str,
    token: AccessToken = Depends(_require_pro_scope),
) -> ProLabExperimentRunResponse:
    if token.actor_id != user_id and token.role != "internal_admin":
        raise HTTPException(status_code=403, detail="Token không được phép xem run của user khác.")
    try:
        return GetProLabRun(runs=_runs()).execute(
            run_id=run_id,
            user_id=user_id,
            include_all=token.role == "internal_admin",
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/experiments/{experiment_id}/report", response_model=ProLabReportExportResponse)
def pro_lab_export_report(
    experiment_id: str,
    user_id: str,
    token: AccessToken = Depends(_require_pro_scope),
) -> ProLabReportExportResponse:
    if token.actor_id != user_id and token.role != "internal_admin":
        raise HTTPException(status_code=403, detail="Token không được phép export report cho user khác.")
    try:
        return ExportExperimentReport(experiments=_experiments(), audit=_audit()).execute(
            user_id=user_id,
            experiment_id=experiment_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/assistant", response_model=AssistantRespondResponse)
def pro_lab_assistant(
    req: AssistantRespondRequest,
    token: AccessToken = Depends(_require_pro_scope),
) -> AssistantRespondResponse:
    if token.actor_id != req.session_id and token.role != "internal_admin":
        raise HTTPException(status_code=403, detail="Token không được phép dùng Pro Assistant cho user khác.")
    return _assistant().execute(
        session_id=req.session_id,
        surface="pro_lab",
        prompt=req.prompt,
        role_hint="pro_assistant",
        conversation_id=req.conversation_id,
        has_pro_scope=True,
    )
