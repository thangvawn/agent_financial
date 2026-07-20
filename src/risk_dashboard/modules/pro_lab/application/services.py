from __future__ import annotations

import os
from dataclasses import replace
from datetime import date, datetime, timezone

from risk_dashboard.modules.analytics_monitoring.application.emitter import emit_product_event
from risk_dashboard.modules.home_onboarding.infrastructure.repositories.sqlite import SqliteOnboardingProfileRepository
from risk_dashboard.modules.pro_lab.domain.entities import (
    ProLabAuditLog,
    ProLabBlueprint,
    ProLabExperiment,
    ProLabExperimentRun,
    ProLabWorkspaceState,
    utc_now_iso,
)
from risk_dashboard.modules.pro_lab.domain.ports import (
    ProLabAuditRepository,
    ProLabBlueprintRepository,
    ProLabExperimentRepository,
    ProLabExperimentRunRepository,
    ProLabWorkspaceStateRepository,
)
from risk_dashboard.modules.pro_lab.infrastructure.repositories.sqlite import (
    new_pro_lab_audit_id,
    new_pro_lab_blueprint_id,
    new_pro_lab_experiment_id,
    new_pro_lab_run_id,
    new_pro_lab_workspace_id,
)
from risk_dashboard.modules.pro_lab.providers.registry import ProLabProviderRegistry
from risk_dashboard.modules.pro_lab.schemas.responses import (
    ProLabAccessTokenResponse,
    ProLabAuditResponse,
    ProLabBlueprintResponse,
    ProLabBlueprintCompareResponse,
    ProLabCatalogResponse,
    ProLabCommandResponse,
    ProLabExperimentResponse,
    ProLabExperimentRunResponse,
    ProLabProviderResponse,
    ProLabReportExportResponse,
    ProLabSessionListResponse,
    ProLabSessionResponse,
    ProLabTeaserResponse,
    ProLabWorkspaceStateResponse,
    ProLabWorkspaceResponse,
)
from risk_dashboard.modules.trust_safety.application.services import TrustSafetyService
from risk_dashboard.platform.security.access_control import SqliteAccessControlRepository, issue_token_for_actor
from risk_dashboard.engines.quant.backtest import run_vn_portfolio_backtest


def is_pro_lab_local_test_open() -> bool:
    explicit = os.getenv("PRO_LAB_LOCAL_TEST_OPEN", "").strip().lower()
    mode = os.getenv("MODE", "").strip().lower()
    if explicit in {"1", "true", "yes", "on"}:
        return True
    return mode in {"development", "dev", "local", "test"}


class GetProLabTeaser:
    def execute(self, *, session_id: str | None = None) -> ProLabTeaserResponse:
        profile = SqliteOnboardingProfileRepository().get(session_id) if session_id else None
        local_test_open = is_pro_lab_local_test_open()
        enabled = bool(os.getenv("PRO_LAB_KEY", "").strip() or os.getenv("ADMIN_TRADING_LAB_KEY", "").strip() or local_test_open)
        pro_eligible = True if local_test_open else bool(profile.pro_eligible) if profile is not None else False
        return ProLabTeaserResponse(
            enabled=enabled,
            pro_eligible=pro_eligible,
            access_mode="local_test_open" if local_test_open else "premium_or_internal",
            positioning="Structured research workspace for serious users; not a retail signal feed.",
            public_boundary=[
                "Insights, Guided Investing and Learn remain the retail-safe surfaces.",
                "Pro Lab is separated so new users are not forced into backtests or strategy complexity.",
            ],
            pro_capabilities=[
                "Natural-language strategy draft",
                "Swarm committee review",
                "Walk-forward + Monte Carlo validation",
                "Risk-budget optimizer",
                "Data source router",
                "Strategy code export",
                "Shadow account journal review",
                "Strategy blueprint",
                "Benchmark studio",
                "Scenario lab",
                "Backtest lab with caveats",
                "Notebook-style experiment output",
            ],
            admin_capabilities=[
                "Experiment log",
                "Audit trail",
                "Internal trading-lab chat",
                "Admin-only strategy design endpoint",
            ],
        )


class GetProLabWorkspace:
    def __init__(self, blueprints: ProLabBlueprintRepository, experiments: ProLabExperimentRepository) -> None:
        self.blueprints = blueprints
        self.experiments = experiments

    def execute(self, *, user_id: str) -> ProLabWorkspaceResponse:
        blueprints = [self._to_blueprint(item) for item in self.blueprints.list_by_user(user_id=user_id)]
        experiments = [self._to_experiment(item) for item in self.experiments.list_by_user(user_id=user_id)]
        emit_product_event(
            event_name="pro_lab_workspace_viewed",
            module="pro_lab",
            surface="pro_lab",
            user_id=user_id,
            properties={"blueprint_count": len(blueprints), "experiment_count": len(experiments)},
        )
        return ProLabWorkspaceResponse(
            enabled=bool(os.getenv("PRO_LAB_KEY", "").strip() or is_pro_lab_local_test_open()),
            access_mode="pro",
            workspace_title="Pro Lab Workspace",
            workspace_summary="Workspace cá nhân để biến ý tưởng trading thành blueprint, swarm review, optimizer, validation, export và journal review trong một luồng làm việc.",
            blueprints=blueprints,
            experiments=experiments,
            capability_cards=[
                {
                    "id": "strategy_copilot",
                    "title": "Strategy Copilot",
                    "summary": "Nhập ý tưởng bằng ngôn ngữ tự nhiên rồi chuyển thành giả thuyết, universe, tín hiệu và validation queue.",
                },
                {
                    "id": "swarm_committee",
                    "title": "Swarm Committee",
                    "summary": "Strategist, quant, risk và execution review cùng một blueprint trước khi backtest hoặc export memo.",
                },
                {
                    "id": "validation_lab",
                    "title": "Validation Lab",
                    "summary": "Chuẩn bị walk-forward, Monte Carlo, transaction-cost và fail conditions trước khi scale strategy.",
                },
                {
                    "id": "optimizer_lab",
                    "title": "Optimizer Lab",
                    "summary": "Tạo allocation draft theo risk budget, max weight, rebalance band và constraint checks.",
                },
                {
                    "id": "export_lab",
                    "title": "Export Lab",
                    "summary": "Xuất strategy skeleton, markdown runbook và checklist để bạn dùng tiếp trong workflow riêng.",
                },
                {
                    "id": "journal_lab",
                    "title": "Journal Lab",
                    "summary": "Đọc nhật ký paper/live để phát hiện rule break, FOMO, oversize và process drift.",
                },
                {
                    "id": "strategy_blueprint",
                    "title": "Strategy Blueprint",
                    "summary": "Bắt đầu từ hypothesis và constraints, không bắt đầu từ tín hiệu mua bán.",
                },
                {
                    "id": "scenario_lab",
                    "title": "Scenario Lab",
                    "summary": "Stress-test giả định vĩ mô để hiểu độ nhạy thay vì đoán tương lai chắc chắn.",
                },
                {
                    "id": "backtest_lab",
                    "title": "Backtest Lab",
                    "summary": "Notebook-style output với benchmark và caveat-first reporting.",
                },
            ],
        )

    def _to_blueprint(self, item: ProLabBlueprint) -> ProLabBlueprintResponse:
        return ProLabBlueprintResponse(
            blueprint_id=item.blueprint_id,
            name=item.name,
            objective=item.objective,
            asset_universe=list(item.asset_universe),
            benchmark=item.benchmark,
            rebalance_frequency=item.rebalance_frequency,
            risk_constraints=item.risk_constraints,
            assumptions_note=item.assumptions_note,
            status=item.status,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def _to_experiment(self, item: ProLabExperiment) -> ProLabExperimentResponse:
        return ProLabExperimentResponse(
            experiment_id=item.experiment_id,
            blueprint_id=item.blueprint_id,
            experiment_type=item.experiment_type,
            status=item.status,
            created_at=item.created_at,
            review_status=item.review_status,
            review_notes=item.review_notes,
            reviewed_at=item.reviewed_at,
            reviewer_id=item.reviewer_id,
            notebook_sections=list(item.output_payload.get("notebook_sections", [])),
            caveats=list(item.output_payload.get("caveats", [])),
            engine_result=item.output_payload.get("engine_result"),
        )


class GetProLabCatalog:
    def __init__(self, registry: ProLabProviderRegistry | None = None) -> None:
        self.registry = registry or ProLabProviderRegistry()

    def execute(self, *, include_private: bool = False) -> ProLabCatalogResponse:
        providers = []
        for provider in self.registry.list(include_private=include_private):
            providers.append(
                ProLabProviderResponse(
                    provider_id=provider.provider_id,
                    label=provider.label,
                    category=provider.category,
                    description=provider.description,
                    enabled=provider.enabled,
                    guardrails=list(provider.guardrails),
                    commands=[
                        ProLabCommandResponse(
                            command_id=command.command_id,
                            label=command.label,
                            description=command.description,
                            input_schema=command.input_schema,
                            output_schema=command.output_schema,
                            risk_level=command.risk_level,
                            async_supported=command.async_supported,
                            requires_review=command.requires_review,
                            public_allowed=command.public_allowed,
                            private_only=command.private_only,
                        )
                        for command in provider.commands
                    ],
                )
            )
        return ProLabCatalogResponse(
            providers=providers,
            private_capabilities_visible=include_private,
            guardrail_summary=[
                "Pro Lab is research/control-plane only, not a public buy/sell signal surface.",
                "Private auto/copy trading commands never place live orders in this MVP.",
                "Critical-risk commands require manual review and audit trail.",
            ],
        )


class RunProLabCommand:
    def __init__(
        self,
        blueprints: ProLabBlueprintRepository,
        experiments: ProLabExperimentRepository,
        runs: ProLabExperimentRunRepository,
        audit: ProLabAuditRepository,
        registry: ProLabProviderRegistry | None = None,
    ) -> None:
        self.blueprints = blueprints
        self.experiments = experiments
        self.runs = runs
        self.audit = audit
        self.registry = registry or ProLabProviderRegistry()

    def execute(
        self,
        *,
        user_id: str,
        provider_id: str,
        command_id: str,
        blueprint_id: str | None,
        input_payload: dict[str, object],
        include_private: bool = False,
        surface: str = "pro",
    ) -> ProLabExperimentRunResponse:
        blueprint = self.blueprints.get(blueprint_id=blueprint_id) if blueprint_id else None
        if blueprint_id and (blueprint is None or blueprint.user_id != user_id):
            raise ValueError("Không tìm thấy blueprint cho user này.")
        provider, command = self.registry.get_command(
            provider_id=provider_id,
            command_id=command_id,
            include_private=include_private,
        )
        result = self.registry.execute(
            provider_id=provider.provider_id,
            command_id=command.command_id,
            input_payload=input_payload,
            blueprint=blueprint,
            include_private=include_private,
        )
        experiment = ProLabExperiment(
            experiment_id=new_pro_lab_experiment_id(),
            user_id=user_id,
            blueprint_id=blueprint_id,
            experiment_type=f"{provider.provider_id}:{command.command_id}",
            status=result.status,
            input_payload={
                "provider_id": provider.provider_id,
                "command_id": command.command_id,
                **input_payload,
            },
            output_payload={
                **result.output_payload,
                "notebook_sections": result.output_payload.get("notebook_sections")
                or result.output_payload.get("report_sections")
                or [
                    {"title": "Command output", "body": "Structured payload is available in the run output."},
                ],
                "caveats": result.output_payload.get("caveats", []),
                "safety_flags": list(result.safety_flags),
                "data_freshness": result.data_freshness,
            },
            review_status="pending_review" if command.requires_review else "approved",
        )
        self.experiments.save(experiment)
        now = utc_now_iso()
        run = ProLabExperimentRun(
            run_id=new_pro_lab_run_id(),
            user_id=user_id,
            experiment_id=experiment.experiment_id,
            blueprint_id=blueprint_id,
            provider_id=provider.provider_id,
            command_id=command.command_id,
            status=result.status,
            input_payload=input_payload,
            output_payload=result.output_payload,
            logs=result.logs,
            progress_pct=result.progress_pct,
            safety_flags=result.safety_flags,
            data_freshness=result.data_freshness,
            created_at=now,
            completed_at=now,
        )
        saved = self.runs.save(run)
        self.audit.save(
            ProLabAuditLog(
                audit_id=new_pro_lab_audit_id(),
                actor_id=user_id,
                surface=surface,
                action="run_provider_command",
                target_type="experiment_run",
                target_id=saved.run_id,
                metadata={
                    "experiment_id": experiment.experiment_id,
                    "provider_id": provider.provider_id,
                    "command_id": command.command_id,
                    "risk_level": command.risk_level,
                    "private_only": command.private_only,
                },
            )
        )
        emit_product_event(
            event_name="pro_lab_provider_command_run",
            module="pro_lab",
            surface="pro_lab",
            user_id=user_id,
            properties={
                "run_id": saved.run_id,
                "provider_id": provider.provider_id,
                "command_id": command.command_id,
                "risk_level": command.risk_level,
                "private_only": command.private_only,
            },
        )
        return _to_run_response(saved)


class GetProLabRun:
    def __init__(self, runs: ProLabExperimentRunRepository) -> None:
        self.runs = runs

    def execute(self, *, run_id: str, user_id: str, include_all: bool = False) -> ProLabExperimentRunResponse:
        run = self.runs.get(run_id=run_id)
        if run is None:
            raise ValueError("Không tìm thấy experiment run.")
        if not include_all and run.user_id != user_id:
            raise PermissionError("Token không được phép xem run này.")
        return _to_run_response(run)


class ListProLabRuns:
    def __init__(self, runs: ProLabExperimentRunRepository) -> None:
        self.runs = runs

    def execute(self, *, user_id: str | None = None) -> list[ProLabExperimentRunResponse]:
        items = self.runs.list_by_user(user_id=user_id) if user_id else self.runs.list_all()
        return [_to_run_response(item) for item in items]


class GetProLabWorkspaceState:
    def __init__(self, workspaces: ProLabWorkspaceStateRepository) -> None:
        self.workspaces = workspaces

    def execute(self, *, user_id: str) -> ProLabWorkspaceStateResponse:
        state = self.workspaces.get(user_id=user_id)
        if state is None:
            state = ProLabWorkspaceState(
                workspace_id=new_pro_lab_workspace_id(),
                user_id=user_id,
                active_page="overview",
                open_panels=("catalog", "experiments"),
                selected_blueprint_id=None,
                selected_experiment_id=None,
                layout={"density": "comfortable", "right_panel": "run_details"},
                notes=None,
            )
            state = self.workspaces.save(state)
        return _to_workspace_state_response(state)


class SaveProLabWorkspaceState:
    def __init__(self, workspaces: ProLabWorkspaceStateRepository, audit: ProLabAuditRepository) -> None:
        self.workspaces = workspaces
        self.audit = audit

    def execute(
        self,
        *,
        user_id: str,
        active_page: str,
        open_panels: list[str],
        selected_blueprint_id: str | None,
        selected_experiment_id: str | None,
        layout: dict[str, object],
        notes: str | None,
        surface: str = "pro",
    ) -> ProLabWorkspaceStateResponse:
        current = self.workspaces.get(user_id=user_id)
        state = ProLabWorkspaceState(
            workspace_id=current.workspace_id if current else new_pro_lab_workspace_id(),
            user_id=user_id,
            active_page=active_page,
            open_panels=tuple(dict.fromkeys(item.strip() for item in open_panels if item.strip())),
            selected_blueprint_id=selected_blueprint_id,
            selected_experiment_id=selected_experiment_id,
            layout=layout,
            notes=notes.strip() if notes else None,
            version=current.version if current else 1,
            updated_at=utc_now_iso(),
        )
        saved = self.workspaces.save(state)
        self.audit.save(
            ProLabAuditLog(
                audit_id=new_pro_lab_audit_id(),
                actor_id=user_id,
                surface=surface,
                action="save_workspace_state",
                target_type="workspace",
                target_id=saved.workspace_id,
                metadata={"active_page": saved.active_page, "version": saved.version},
            )
        )
        return _to_workspace_state_response(saved)


class SaveStrategyBlueprint:
    def __init__(self, blueprints: ProLabBlueprintRepository, audit: ProLabAuditRepository) -> None:
        self.blueprints = blueprints
        self.audit = audit

    def execute(
        self,
        *,
        user_id: str,
        name: str,
        objective: str,
        asset_universe: list[str],
        benchmark: str,
        rebalance_frequency: str,
        risk_constraints: str,
        assumptions_note: str | None,
        surface: str = "pro",
    ) -> ProLabBlueprintResponse:
        now = utc_now_iso()
        blueprint = ProLabBlueprint(
            blueprint_id=new_pro_lab_blueprint_id(),
            user_id=user_id,
            name=name.strip(),
            objective=objective.strip(),
            asset_universe=tuple(dict.fromkeys(item.upper().strip() for item in asset_universe if item.strip())),
            benchmark=benchmark.strip().upper(),
            rebalance_frequency=rebalance_frequency.strip(),
            risk_constraints=risk_constraints.strip(),
            assumptions_note=assumptions_note.strip() if assumptions_note else None,
            status="draft",
            created_at=now,
            updated_at=now,
        )
        saved = self.blueprints.save(blueprint)
        self.audit.save(
            ProLabAuditLog(
                audit_id=new_pro_lab_audit_id(),
                actor_id=user_id,
                surface=surface,
                action="save_blueprint",
                target_type="blueprint",
                target_id=saved.blueprint_id,
                metadata={"asset_count": len(saved.asset_universe), "benchmark": saved.benchmark},
            )
        )
        emit_product_event(
            event_name="pro_lab_blueprint_created",
            module="pro_lab",
            surface="pro_lab",
            user_id=user_id,
            properties={"blueprint_id": saved.blueprint_id, "benchmark": saved.benchmark},
        )
        return GetProLabWorkspace(self.blueprints, _EmptyExperimentRepo())._to_blueprint(saved)


class UpdateStrategyBlueprint:
    def __init__(self, blueprints: ProLabBlueprintRepository, audit: ProLabAuditRepository) -> None:
        self.blueprints = blueprints
        self.audit = audit

    def execute(
        self,
        *,
        blueprint_id: str,
        user_id: str,
        name: str | None,
        objective: str | None,
        asset_universe: list[str] | None,
        benchmark: str | None,
        rebalance_frequency: str | None,
        risk_constraints: str | None,
        assumptions_note: str | None,
        surface: str = "pro",
    ) -> ProLabBlueprintResponse:
        blueprint = self.blueprints.get(blueprint_id=blueprint_id)
        if blueprint is None or blueprint.user_id != user_id:
            raise ValueError("Không tìm thấy blueprint để cập nhật.")
        updated = replace(
            blueprint,
            name=name.strip() if name is not None else blueprint.name,
            objective=objective.strip() if objective is not None else blueprint.objective,
            asset_universe=(
                tuple(dict.fromkeys(item.upper().strip() for item in asset_universe if item.strip()))
                if asset_universe is not None
                else blueprint.asset_universe
            ),
            benchmark=benchmark.strip().upper() if benchmark is not None else blueprint.benchmark,
            rebalance_frequency=rebalance_frequency.strip() if rebalance_frequency is not None else blueprint.rebalance_frequency,
            risk_constraints=risk_constraints.strip() if risk_constraints is not None else blueprint.risk_constraints,
            assumptions_note=assumptions_note.strip() if assumptions_note is not None else blueprint.assumptions_note,
            updated_at=utc_now_iso(),
        )
        saved = self.blueprints.save(updated)
        self.audit.save(
            ProLabAuditLog(
                audit_id=new_pro_lab_audit_id(),
                actor_id=user_id,
                surface=surface,
                action="update_blueprint",
                target_type="blueprint",
                target_id=saved.blueprint_id,
                metadata={"status": saved.status},
            )
        )
        emit_product_event(
            event_name="pro_lab_blueprint_updated",
            module="pro_lab",
            surface="pro_lab",
            user_id=user_id,
            properties={"blueprint_id": saved.blueprint_id, "status": saved.status},
        )
        return GetProLabWorkspace(self.blueprints, _EmptyExperimentRepo())._to_blueprint(saved)


class ArchiveStrategyBlueprint:
    def __init__(self, blueprints: ProLabBlueprintRepository, audit: ProLabAuditRepository) -> None:
        self.blueprints = blueprints
        self.audit = audit

    def execute(self, *, blueprint_id: str, user_id: str, surface: str = "pro") -> ProLabBlueprintResponse:
        blueprint = self.blueprints.get(blueprint_id=blueprint_id)
        if blueprint is None or blueprint.user_id != user_id:
            raise ValueError("Không tìm thấy blueprint để archive.")
        archived = replace(blueprint, status="archived", updated_at=utc_now_iso())
        saved = self.blueprints.save(archived)
        self.audit.save(
            ProLabAuditLog(
                audit_id=new_pro_lab_audit_id(),
                actor_id=user_id,
                surface=surface,
                action="archive_blueprint",
                target_type="blueprint",
                target_id=saved.blueprint_id,
                metadata={"status": saved.status},
            )
        )
        emit_product_event(
            event_name="pro_lab_blueprint_archived",
            module="pro_lab",
            surface="pro_lab",
            user_id=user_id,
            properties={"blueprint_id": saved.blueprint_id},
        )
        return GetProLabWorkspace(self.blueprints, _EmptyExperimentRepo())._to_blueprint(saved)


class CompareStrategyBlueprints:
    def __init__(self, blueprints: ProLabBlueprintRepository, audit: ProLabAuditRepository) -> None:
        self.blueprints = blueprints
        self.audit = audit

    def execute(self, *, user_id: str, left_id: str, right_id: str, surface: str = "pro") -> ProLabBlueprintCompareResponse:
        left = self.blueprints.get(blueprint_id=left_id)
        right = self.blueprints.get(blueprint_id=right_id)
        if left is None or right is None or left.user_id != user_id or right.user_id != user_id:
            raise ValueError("Không tìm thấy đủ hai blueprint để compare.")
        differences = [
            {"field": "benchmark", "left": left.benchmark, "right": right.benchmark},
            {"field": "rebalance_frequency", "left": left.rebalance_frequency, "right": right.rebalance_frequency},
            {"field": "risk_constraints", "left": left.risk_constraints, "right": right.risk_constraints},
            {"field": "asset_count", "left": str(len(left.asset_universe)), "right": str(len(right.asset_universe))},
            {"field": "status", "left": left.status, "right": right.status},
        ]
        self.audit.save(
            ProLabAuditLog(
                audit_id=new_pro_lab_audit_id(),
                actor_id=user_id,
                surface=surface,
                action="compare_blueprints",
                target_type="blueprint_compare",
                target_id=f"{left_id}:{right_id}",
                metadata={"left_id": left_id, "right_id": right_id},
            )
        )
        emit_product_event(
            event_name="pro_lab_blueprint_compared",
            module="pro_lab",
            surface="pro_lab",
            user_id=user_id,
            properties={"left_blueprint_id": left_id, "right_blueprint_id": right_id},
        )
        return ProLabBlueprintCompareResponse(
            left_blueprint_id=left_id,
            right_blueprint_id=right_id,
            summary="So sánh này để review benchmark, cadence, risk constraints và shape của asset universe; không phải để tuyên bố chiến lược nào thắng chắc.",
            differences=differences,
        )


class RunScenarioLab:
    def __init__(
        self,
        blueprints: ProLabBlueprintRepository,
        experiments: ProLabExperimentRepository,
        audit: ProLabAuditRepository,
    ) -> None:
        self.blueprints = blueprints
        self.experiments = experiments
        self.audit = audit

    def execute(
        self,
        *,
        user_id: str,
        blueprint_id: str,
        scenario_preset: str,
        usd_vnd_rate: float | None,
        sbv_interest_rate_pct: float | None,
        surface: str = "pro",
    ) -> ProLabExperimentResponse:
        blueprint = self.blueprints.get(blueprint_id=blueprint_id)
        if blueprint is None or blueprint.user_id != user_id:
            raise ValueError("Không tìm thấy blueprint cho user này.")
        scenario_note = self._build_scenario_note(
            scenario_preset=scenario_preset,
            usd_vnd_rate=usd_vnd_rate,
            sbv_interest_rate_pct=sbv_interest_rate_pct,
        )
        experiment = ProLabExperiment(
            experiment_id=new_pro_lab_experiment_id(),
            user_id=user_id,
            blueprint_id=blueprint_id,
            experiment_type="scenario_lab",
            status="completed",
            input_payload={
                "scenario_preset": scenario_preset,
                "usd_vnd_rate": usd_vnd_rate,
                "sbv_interest_rate_pct": sbv_interest_rate_pct,
            },
            output_payload={
                "notebook_sections": [
                    {"title": "Objective", "body": blueprint.objective},
                    {"title": "Scenario setup", "body": scenario_note["setup"]},
                    {"title": "Why it matters", "body": scenario_note["why_it_matters"]},
                    {"title": "What to review", "body": scenario_note["what_to_review"]},
                ],
                "caveats": [
                    "Scenario lab để hiểu độ nhạy, không phải dự báo chắc chắn.",
                    "Nếu muốn advisory-style output, không nên dùng Pro Lab như retail signal engine.",
                ],
            },
        )
        self.experiments.save(experiment)
        self.audit.save(
            ProLabAuditLog(
                audit_id=new_pro_lab_audit_id(),
                actor_id=user_id,
                surface=surface,
                action="run_scenario_lab",
                target_type="experiment",
                target_id=experiment.experiment_id,
                metadata=experiment.input_payload,
            )
        )
        emit_product_event(
            event_name="pro_lab_experiment_run",
            module="pro_lab",
            surface="pro_lab",
            user_id=user_id,
            properties={"experiment_id": experiment.experiment_id, "scenario_type": scenario_preset},
        )
        return GetProLabWorkspace(self.blueprints, self.experiments)._to_experiment(experiment)

    def _build_scenario_note(self, *, scenario_preset: str, usd_vnd_rate: float | None, sbv_interest_rate_pct: float | None) -> dict[str, str]:
        if scenario_preset == "fx_stress":
            return {
                "setup": f"FX stress với USD/VND {usd_vnd_rate or 'không override'} và focus vào mức nhạy đa tiền tệ.",
                "why_it_matters": "Kịch bản này hữu ích khi blueprint nhạy với chi phí vốn, remittance hoặc earnings translation.",
                "what_to_review": "Review benchmark, concentration và giả định thanh khoản trước khi đọc kết quả quá mạnh tay.",
            }
        if scenario_preset == "rate_hike":
            return {
                "setup": f"Rate hike với SBV policy rate {sbv_interest_rate_pct or 'không override'}%.",
                "why_it_matters": "Kịch bản này giúp xem chiến lược nhạy thế nào với chi phí vốn và compressing valuations.",
                "what_to_review": "Review drawdown tolerance, leverage-sensitive tickers và benchmark spread.",
            }
        return {
            "setup": "Risk-off preset để mô phỏng môi trường thận trọng hơn bình thường.",
            "why_it_matters": "Phù hợp khi user muốn nhìn chiến lược dưới áp lực thanh khoản và tâm lý risk-off.",
            "what_to_review": "Xem lại diversification, benchmark và cadence rebalance.",
        }


class RunBacktestLab:
    def __init__(
        self,
        blueprints: ProLabBlueprintRepository,
        experiments: ProLabExperimentRepository,
        audit: ProLabAuditRepository,
    ) -> None:
        self.blueprints = blueprints
        self.experiments = experiments
        self.audit = audit

    def execute(
        self,
        *,
        user_id: str,
        blueprint_id: str,
        start_date: str,
        end_date: str,
        initial_capital: float,
        timeframe: str = "1d",
        commission_pct: float = 0.0,
        slippage_pct: float = 0.0,
        strategy_text: str | None = None,
        surface: str = "pro",
    ) -> ProLabExperimentResponse:
        blueprint = self.blueprints.get(blueprint_id=blueprint_id)
        if blueprint is None or blueprint.user_id != user_id:
            raise ValueError("Không tìm thấy blueprint cho user này.")
        start_day = _parse_iso_date(start_date, field_name="start_date")
        end_day = _parse_iso_date(end_date, field_name="end_date")
        try:
            result = run_vn_portfolio_backtest(
                list(blueprint.asset_universe),
                start_day,
                end_day,
                initial_capital,
                equal_weight=True,
                include_benchmark=True,
                strategy=_strategy_config_from_text(strategy_text),
                interval=timeframe,
            )
        except Exception as exc:
            # Keep the workspace usable in offline/test environments where
            # market data providers are unavailable.
            result = _build_offline_backtest_result(
                tickers=list(blueprint.asset_universe),
                start_date=start_day,
                end_date=end_day,
                initial_capital=initial_capital,
                timeframe=timeframe,
                reason=str(exc),
            )
        result = {
            **result,
            "execution_costs": {
                "commission_pct": float(commission_pct),
                "slippage_pct": float(slippage_pct),
                "mode": "captured_for_research_context",
            },
            "strategy_text": strategy_text.strip() if strategy_text else None,
        }
        metrics = result.get("metrics", {})
        warnings = result.get("warnings", [])
        final_value = _last_equity_value(result)
        total_return = metrics.get("total_return_pct")
        max_drawdown = metrics.get("max_drawdown_pct")
        sharpe = metrics.get("sharpe") or metrics.get("sharpe_ratio")
        experiment = ProLabExperiment(
            experiment_id=new_pro_lab_experiment_id(),
            user_id=user_id,
            blueprint_id=blueprint_id,
            experiment_type="backtest_lab",
            status="completed",
            input_payload={
                "start_date": start_date,
                "end_date": end_date,
                "initial_capital": initial_capital,
                "timeframe": timeframe,
                "commission_pct": commission_pct,
                "slippage_pct": slippage_pct,
                "strategy_text": strategy_text,
            },
            output_payload={
                "notebook_sections": [
                    {"title": "Objective", "body": blueprint.objective},
                    {
                        "title": "Setup",
                        "body": (
                            f"Backtest chạy trên dữ liệu giá lịch sử {timeframe} từ {start_date} đến {end_date}, "
                            f"benchmark VN-Index khi tải được, danh mục equal-weight theo blueprint. "
                            f"Cost context: commission {commission_pct:.2f}%, slippage {slippage_pct:.2f}%."
                        ),
                    },
                    {
                        "title": "Kết quả định lượng",
                        "body": (
                            f"Final value: {_format_metric(final_value)}; total return: {_format_pct(total_return)}; "
                            f"max drawdown: {_format_pct(max_drawdown)}; Sharpe: {_format_metric(sharpe)}."
                        ),
                    },
                    {
                        "title": "Dữ liệu và cảnh báo",
                        "body": (
                            f"Nguồn: {result.get('source', 'historical price feed')}. "
                            f"Warnings: {'; '.join(str(item) for item in warnings) if warnings else 'không có cảnh báo lớn từ engine.'}"
                        ),
                    },
                    {
                        "title": "Caveat-first reading",
                        "body": "Kết quả này là mô phỏng lịch sử để sinh viên đọc giả định, benchmark và drawdown; không phải dự báo hay khuyến nghị giao dịch.",
                    },
                ],
                "caveats": [
                    "Backtest hiện là buy-and-hold equal-weight trừ khi strategy text map được sang rule engine nội bộ; phí/trượt giá đang được ghi nhận như context nghiên cứu, chưa trừ trực tiếp khỏi mọi nhánh engine.",
                    "Không nên biến output này thành public marketing claim hay trade signal.",
                ],
                "engine_result": result,
            },
        )
        self.experiments.save(experiment)
        self.audit.save(
            ProLabAuditLog(
                audit_id=new_pro_lab_audit_id(),
                actor_id=user_id,
                surface=surface,
                action="run_backtest_lab",
                target_type="experiment",
                target_id=experiment.experiment_id,
                metadata=experiment.input_payload,
            )
        )
        emit_product_event(
            event_name="pro_lab_experiment_run",
            module="pro_lab",
            surface="pro_lab",
            user_id=user_id,
            properties={"experiment_id": experiment.experiment_id, "scenario_type": "backtest_lab"},
        )
        return GetProLabWorkspace(self.blueprints, self.experiments)._to_experiment(experiment)


def _last_equity_value(result: dict[str, object]) -> object:
    series = result.get("series")
    if isinstance(series, dict):
        portfolio = series.get("portfolio")
        if isinstance(portfolio, list) and portfolio:
            last = portfolio[-1]
            if isinstance(last, dict):
                return last.get("value")
    if isinstance(series, list) and series:
        last = series[-1]
        if isinstance(last, dict):
            return last.get("portfolio_value") or last.get("equity") or last.get("value")
    return None


def _build_offline_backtest_result(
    *,
    tickers: list[str],
    start_date: date,
    end_date: date,
    initial_capital: float,
    timeframe: str,
    reason: str,
) -> dict[str, object]:
    normalized = [item.strip().upper() for item in tickers if item and item.strip()]
    asset_count = max(len(normalized), 1)
    start_ts = _to_unix_seconds(start_date)
    end_ts = _to_unix_seconds(end_date)
    warning = (
        "Historical market feed unavailable, so Pro Lab returned an offline educational fallback. "
        f"Original engine message: {reason}"
    )
    return {
        "tickers": normalized,
        "weights": {ticker: round(1 / asset_count, 6) for ticker in normalized},
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "interval": timeframe,
        "initial_capital": float(initial_capital),
        "metrics": {
            "final_value": float(initial_capital),
            "ending_value": float(initial_capital),
            "total_return_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "sharpe": 0.0,
            "trading_days": 2,
        },
        "series": {
            "portfolio": [
                {"time": start_ts, "value": float(initial_capital)},
                {"time": end_ts, "value": float(initial_capital)},
            ]
        },
        "monthly_returns": [],
        "ath_segments": [],
        "benchmark_label": None,
        "warnings": [warning],
        "source": "offline_fallback",
    }


def _strategy_config_from_text(strategy_text: str | None) -> dict[str, float] | None:
    text = (strategy_text or "").lower()
    if not text:
        return None
    if "volume" not in text and "btc" not in text and "stop" not in text:
        return None
    return {
        "volume_spike_multiplier": 2.0,
        "btc_daily_change_min_pct": 3.0,
        "stop_loss_pct": 4.0,
    }


def _to_unix_seconds(value: date) -> int:
    return int(datetime(value.year, value.month, value.day, tzinfo=timezone.utc).timestamp())


def _parse_iso_date(value: str, *, field_name: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} phải có định dạng YYYY-MM-DD.") from exc


def _format_metric(value: object) -> str:
    if value is None:
        return "n/a"
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _format_pct(value: object) -> str:
    if value is None:
        return "n/a"
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return str(value)


class ListAuditLogs:
    def __init__(self, audit: ProLabAuditRepository) -> None:
        self.audit = audit

    def execute(self) -> list[ProLabAuditResponse]:
        return [
            ProLabAuditResponse(
                audit_id=item.audit_id,
                actor_id=item.actor_id,
                surface=item.surface,
                action=item.action,
                target_type=item.target_type,
                target_id=item.target_id,
                metadata=item.metadata,
                created_at=item.created_at,
            )
            for item in self.audit.list_all()
        ]


class ListProLabSessions:
    def __init__(self, access_control: SqliteAccessControlRepository) -> None:
        self.access_control = access_control

    def execute(self, *, actor_id: str, current_token_id: str | None = None) -> ProLabSessionListResponse:
        sessions = [
            ProLabSessionResponse(
                token_id=item.token_id,
                actor_id=item.actor_id,
                role=item.role,
                status=item.status,
                scopes=list(item.scopes),
                created_at=item.created_at,
                expires_at=item.expires_at,
                is_current=item.token_id == current_token_id,
            )
            for item in self.access_control.list_tokens(actor_id=actor_id)
        ]
        return ProLabSessionListResponse(
            actor_id=actor_id,
            current_token_id=current_token_id,
            sessions=sessions,
        )


class RevokeProLabSession:
    def __init__(self, access_control: SqliteAccessControlRepository, audit: ProLabAuditRepository) -> None:
        self.access_control = access_control
        self.audit = audit

    def execute(
        self,
        *,
        actor_id: str,
        token_id: str,
        revoked_by: str,
        surface: str = "pro",
    ) -> ProLabSessionResponse:
        token = self.access_control.get_token(token_id=token_id)
        if token is None or token.actor_id != actor_id:
            raise ValueError("Không tìm thấy session/token để revoke.")
        revoked = self.access_control.revoke_token(token_id=token_id)
        if revoked is None:
            raise ValueError("Không thể revoke token.")
        self.audit.save(
            ProLabAuditLog(
                audit_id=new_pro_lab_audit_id(),
                actor_id=revoked_by,
                surface=surface,
                action="revoke_session",
                target_type="access_token",
                target_id=token_id,
                metadata={"session_owner": actor_id, "role": revoked.role},
            )
        )
        emit_product_event(
            event_name="pro_lab_session_revoked",
            module="pro_lab",
            surface="pro_lab",
            user_id=actor_id,
            properties={"token_id": token_id},
        )
        return ProLabSessionResponse(
            token_id=revoked.token_id,
            actor_id=revoked.actor_id,
            role=revoked.role,
            status=revoked.status,
            scopes=list(revoked.scopes),
            created_at=revoked.created_at,
            expires_at=revoked.expires_at,
            is_current=False,
        )


class ReviewProLabExperiment:
    def __init__(self, experiments: ProLabExperimentRepository, audit: ProLabAuditRepository) -> None:
        self.experiments = experiments
        self.audit = audit

    def execute(
        self,
        *,
        experiment_id: str,
        review_status: str,
        review_notes: str | None,
        reviewer_id: str,
        surface: str = "admin",
    ) -> ProLabExperimentResponse:
        normalized = review_status.strip().lower()
        if normalized not in {"approved", "needs_changes", "rejected"}:
            raise ValueError("review_status phải là approved, needs_changes hoặc rejected.")
        reviewed = self.experiments.review(
            experiment_id=experiment_id,
            review_status=normalized,
            review_notes=review_notes.strip() if review_notes else None,
            reviewer_id=reviewer_id,
        )
        if reviewed is None:
            raise ValueError("Không tìm thấy experiment để review.")
        self.audit.save(
            ProLabAuditLog(
                audit_id=new_pro_lab_audit_id(),
                actor_id=reviewer_id,
                surface=surface,
                action="review_experiment",
                target_type="experiment",
                target_id=experiment_id,
                metadata={"review_status": normalized},
            )
        )
        emit_product_event(
            event_name="pro_lab_admin_review_completed",
            module="pro_lab",
            surface="pro_lab_admin",
            user_id=reviewer_id,
            properties={"experiment_id": experiment_id, "review_status": normalized},
        )
        return GetProLabWorkspace(_EmptyBlueprintRepo(), self.experiments)._to_experiment(reviewed)


class ExportExperimentReport:
    def __init__(self, experiments: ProLabExperimentRepository, audit: ProLabAuditRepository) -> None:
        self.experiments = experiments
        self.audit = audit
        self.trust = TrustSafetyService()

    def execute(self, *, user_id: str, experiment_id: str, surface: str = "pro") -> ProLabReportExportResponse:
        experiment = next((item for item in self.experiments.list_by_user(user_id=user_id) if item.experiment_id == experiment_id), None)
        if experiment is None:
            raise ValueError("Không tìm thấy experiment để export.")
        quality_state = "good" if experiment.review_status == "approved" else "low_confidence"
        presentation = self.trust.build_presentation(
            surface="pro_lab",
            topic=experiment.experiment_type,
            quality_state=quality_state,
            freshness_value=None,
            disclaimer=None,
        )
        lines = [
            f"# Pro Lab Report: {experiment.experiment_type}",
            "",
            f"- Experiment ID: {experiment.experiment_id}",
            f"- Blueprint ID: {experiment.blueprint_id or 'n/a'}",
            f"- Created at: {experiment.created_at}",
            f"- Review status: {experiment.review_status}",
            f"- Confidence label: {presentation.confidence_label}",
            "",
            "## What This Is",
            "",
            presentation.what_this_is,
            "",
            "## What This Is Not",
            "",
            presentation.what_this_is_not,
            "",
            "## Trust & Safety",
            "",
            f"- {presentation.disclaimer.title}: {presentation.disclaimer.short_text}",
        ]
        if presentation.risk_banner:
            lines.extend(["", f"- Risk banner: {presentation.risk_banner}"])
        lines.extend([
            "",
            "## Input",
            "",
        ])
        for key, value in experiment.input_payload.items():
            lines.append(f"- {key}: {value}")
        lines.extend(["", "## Notebook Sections", ""])
        for section in experiment.output_payload.get("notebook_sections", []):
            lines.append(f"### {section.get('title', 'Section')}")
            lines.append(str(section.get("body", "")))
            lines.append("")
        caveats = experiment.output_payload.get("caveats", [])
        if caveats:
            lines.extend(["## Caveats", ""])
            for item in caveats:
                lines.append(f"- {item}")
        content = "\n".join(lines).strip()
        self.audit.save(
            ProLabAuditLog(
                audit_id=new_pro_lab_audit_id(),
                actor_id=user_id,
                surface=surface,
                action="export_report",
                target_type="experiment",
                target_id=experiment_id,
                metadata={"experiment_type": experiment.experiment_type},
            )
        )
        emit_product_event(
            event_name="pro_lab_report_exported",
            module="pro_lab",
            surface="pro_lab",
            user_id=user_id,
            properties={"experiment_id": experiment_id, "review_status": experiment.review_status},
        )
        self.trust.record_audit(
            actor_id=user_id,
            surface="pro_lab",
            topic=experiment.experiment_type,
            channel="report_export",
            risk_classes=tuple(
                label
                for label in (
                    "missing_disclaimer" if presentation.disclaimer_injected else "",
                    "model_hallucination" if experiment.review_status != "approved" else "",
                )
                if label
            ),
            route_decision="exported_pro_report",
            output_summary=experiment.experiment_id,
            disclaimer_injected=presentation.disclaimer_injected,
            confidence_label=presentation.confidence_label,
            escalation_action="review_before_external_use" if experiment.review_status != "approved" else None,
        )
        return ProLabReportExportResponse(
            export_id=experiment.experiment_id,
            filename=f"pro-lab-report-{experiment.experiment_id}.md",
            content_type="text/markdown",
            content=content,
            confidence_label=presentation.confidence_label,
            disclaimer_title=presentation.disclaimer.title,
            disclaimer_text=presentation.disclaimer.short_text,
            risk_banner=presentation.risk_banner,
            what_this_is=presentation.what_this_is,
            what_this_is_not=presentation.what_this_is_not,
            generated_at=utc_now_iso(),
        )


class IssueProLabAccessToken:
    def execute(self, *, actor_id: str, role: str) -> ProLabAccessTokenResponse:
        token = issue_token_for_actor(actor_id=actor_id, role=role)
        return ProLabAccessTokenResponse(
            actor_id=token.actor_id,
            role=token.role,
            access_token=token.token_id,
            scopes=list(token.scopes),
            expires_at=token.expires_at,
        )


def _to_run_response(item: ProLabExperimentRun) -> ProLabExperimentRunResponse:
    return ProLabExperimentRunResponse(
        run_id=item.run_id,
        user_id=item.user_id,
        experiment_id=item.experiment_id,
        blueprint_id=item.blueprint_id,
        provider_id=item.provider_id,
        command_id=item.command_id,
        status=item.status,
        input_payload=item.input_payload,
        output_payload=item.output_payload,
        logs=list(item.logs),
        progress_pct=item.progress_pct,
        safety_flags=list(item.safety_flags),
        data_freshness=item.data_freshness,
        created_at=item.created_at,
        completed_at=item.completed_at,
    )


def _to_workspace_state_response(item: ProLabWorkspaceState) -> ProLabWorkspaceStateResponse:
    return ProLabWorkspaceStateResponse(
        workspace_id=item.workspace_id,
        user_id=item.user_id,
        active_page=item.active_page,
        open_panels=list(item.open_panels),
        selected_blueprint_id=item.selected_blueprint_id,
        selected_experiment_id=item.selected_experiment_id,
        layout=item.layout,
        notes=item.notes,
        version=item.version,
        updated_at=item.updated_at,
    )


class _EmptyExperimentRepo(ProLabExperimentRepository):
    def save(self, experiment: ProLabExperiment) -> ProLabExperiment:
        return experiment

    def list_by_user(self, *, user_id: str) -> list[ProLabExperiment]:
        return []

    def list_all(self) -> list[ProLabExperiment]:
        return []

    def get(self, *, experiment_id: str) -> ProLabExperiment | None:
        return None

    def review(
        self,
        *,
        experiment_id: str,
        review_status: str,
        review_notes: str | None,
        reviewer_id: str,
    ) -> ProLabExperiment | None:
        return None


class _EmptyBlueprintRepo(ProLabBlueprintRepository):
    def save(self, blueprint: ProLabBlueprint) -> ProLabBlueprint:
        return blueprint

    def list_by_user(self, *, user_id: str) -> list[ProLabBlueprint]:
        return []

    def get(self, *, blueprint_id: str) -> ProLabBlueprint | None:
        return None
