from __future__ import annotations

from datetime import datetime, timezone

from risk_dashboard.modules.pro_lab.domain.entities import ProLabBlueprint
from risk_dashboard.modules.pro_lab.providers.contracts import (
    ProLabCommandDefinition,
    ProLabProviderDefinition,
    ProLabProviderResult,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _object_schema(properties: dict[str, object]) -> dict[str, object]:
    return {"type": "object", "properties": properties}


def _strategy_code_template(*, target: str, universe: list[str]) -> str:
    tickers = ", ".join(repr(item) for item in universe)
    if target == "pine":
        return """//@version=5
strategy("Northstar strategy skeleton", overlay=true)
fast = ta.sma(close, 20)
slow = ta.sma(close, 60)
entry = ta.crossover(fast, slow)
exit = ta.crossunder(fast, slow)
if entry
    strategy.entry("research-long", strategy.long)
if exit
    strategy.close("research-long")
"""
    return f"""UNIVERSE = [{tickers}]

def signal(row):
    quality_ok = row.get("quality_score", 0) >= 70
    momentum_ok = row.get("momentum_60d", 0) > 0
    drawdown_ok = row.get("drawdown_pct", 0) > -12
    return quality_ok and momentum_ok and drawdown_ok

def position_size(account_equity, risk_budget_pct=2, stop_loss_pct=8):
    risk_amount = account_equity * risk_budget_pct / 100
    return risk_amount / max(stop_loss_pct / 100, 0.01)
"""


class ProLabProviderRegistry:
    def __init__(self) -> None:
        self._providers = {
            item.provider_id: item
            for item in (
                ProLabProviderDefinition(
                    provider_id="strategy_copilot",
                    label="Strategy Copilot",
                    category="strategy_design",
                    description="Turn a natural-language research idea into a testable strategy blueprint draft.",
                    enabled=True,
                    guardrails=(
                        "Natural-language strategy drafts must be validated before use.",
                        "Generated rules are research hypotheses, not instructions to trade.",
                    ),
                    commands=(
                        ProLabCommandDefinition(
                            command_id="natural_language_strategy",
                            label="Natural-language strategy",
                            description="Convert an investment idea into universe, signal, risk and validation notes.",
                            input_schema=_object_schema(
                                {
                                    "idea": {"type": "string"},
                                    "market": {"type": "string"},
                                    "horizon": {"type": "string"},
                                    "risk_budget_pct": {"type": "number"},
                                }
                            ),
                            output_schema=_object_schema({"strategy_draft": {"type": "object"}, "validation_queue": {"type": "array"}}),
                            risk_level="medium",
                        ),
                    ),
                ),
                ProLabProviderDefinition(
                    provider_id="swarm_committee",
                    label="Swarm Committee",
                    category="research_review",
                    description="Run a structured multi-role review before scenario, backtest or memo export.",
                    enabled=True,
                    guardrails=(
                        "Committee output is a debate and checklist, not a final portfolio decision.",
                        "Every role must surface caveats and unresolved questions.",
                    ),
                    commands=(
                        ProLabCommandDefinition(
                            command_id="quant_strategy_review",
                            label="Quant strategy review",
                            description="Review a blueprint with strategist, quant, risk and execution roles.",
                            input_schema=_object_schema(
                                {
                                    "review_focus": {"type": "string"},
                                    "validation_depth": {"type": "string"},
                                }
                            ),
                            output_schema=_object_schema({"role_memos": {"type": "array"}, "signoff_checklist": {"type": "array"}}),
                            risk_level="high",
                        ),
                    ),
                ),
                ProLabProviderDefinition(
                    provider_id="scenario_lab",
                    label="Scenario Lab",
                    category="research",
                    description="Stress-test macro and portfolio assumptions without making predictions.",
                    enabled=True,
                    guardrails=(
                        "Scenario output is sensitivity analysis, not a forecast.",
                        "Use stale-data and concentration warnings before reading results as strong evidence.",
                    ),
                    commands=(
                        ProLabCommandDefinition(
                            command_id="fx_rate_stress",
                            label="FX / rate stress",
                            description="Review how a blueprint behaves under FX and policy-rate pressure.",
                            input_schema=_object_schema(
                                {
                                    "usd_vnd_rate": {"type": "number"},
                                    "policy_rate_pct": {"type": "number"},
                                    "shock_label": {"type": "string"},
                                }
                            ),
                            output_schema=_object_schema({"notebook_sections": {"type": "array"}}),
                            risk_level="medium",
                        ),
                    ),
                ),
                ProLabProviderDefinition(
                    provider_id="backtest_lab",
                    label="Backtest Lab",
                    category="research",
                    description="Run simplified benchmark-aware backtest notes with caveat-first reporting.",
                    enabled=True,
                    guardrails=(
                        "Backtest results are historical sandbox evidence, not future performance.",
                        "Lookahead bias, survivorship bias and execution assumptions must be reviewed.",
                    ),
                    commands=(
                        ProLabCommandDefinition(
                            command_id="benchmark_sandbox",
                            label="Benchmark sandbox",
                            description="Generate a notebook-style benchmark comparison for a blueprint.",
                            input_schema=_object_schema(
                                {
                                    "start_date": {"type": "string"},
                                    "end_date": {"type": "string"},
                                    "initial_capital": {"type": "number"},
                                }
                            ),
                            output_schema=_object_schema({"metrics": {"type": "object"}, "notebook_sections": {"type": "array"}}),
                            risk_level="high",
                        ),
                    ),
                ),
                ProLabProviderDefinition(
                    provider_id="validation_lab",
                    label="Validation Lab",
                    category="validation",
                    description="Stress-test a strategy with walk-forward, Monte Carlo and overfit diagnostics.",
                    enabled=True,
                    guardrails=(
                        "Validation output highlights weak points before capital is allocated.",
                        "Use failed checks as blockers, not as cosmetic warnings.",
                    ),
                    commands=(
                        ProLabCommandDefinition(
                            command_id="walk_forward_monte_carlo",
                            label="Walk-forward + Monte Carlo",
                            description="Create a validation checklist with rolling windows, cost sensitivity and randomized trade-order stress.",
                            input_schema=_object_schema(
                                {
                                    "window_months": {"type": "number"},
                                    "cost_bps": {"type": "number"},
                                    "simulations": {"type": "number"},
                                }
                            ),
                            output_schema=_object_schema({"validation_suite": {"type": "array"}, "fail_conditions": {"type": "array"}}),
                            risk_level="high",
                        ),
                    ),
                ),
                ProLabProviderDefinition(
                    provider_id="optimizer_lab",
                    label="Optimizer Lab",
                    category="portfolio_construction",
                    description="Draft allocation plans with risk parity, max weight and turnover controls.",
                    enabled=True,
                    guardrails=(
                        "Optimizer output must respect liquidity, concentration and user-defined exclusions.",
                        "Expected return assumptions should be treated as editable inputs.",
                    ),
                    commands=(
                        ProLabCommandDefinition(
                            command_id="risk_budget_optimizer",
                            label="Risk-budget optimizer",
                            description="Generate an allocation draft from blueprint universe and risk budget constraints.",
                            input_schema=_object_schema(
                                {
                                    "method": {"type": "string"},
                                    "max_weight_pct": {"type": "number"},
                                    "target_volatility_pct": {"type": "number"},
                                }
                            ),
                            output_schema=_object_schema({"allocation": {"type": "array"}, "constraint_checks": {"type": "array"}}),
                            risk_level="high",
                        ),
                    ),
                ),
                ProLabProviderDefinition(
                    provider_id="data_router",
                    label="Data Router",
                    category="data_quality",
                    description="Inspect source coverage, freshness and fallback order before running an experiment.",
                    enabled=True,
                    guardrails=(
                        "Data coverage should be checked before strategy claims are trusted.",
                        "Missing fields should degrade the workflow instead of silently filling values.",
                    ),
                    commands=(
                        ProLabCommandDefinition(
                            command_id="source_health_check",
                            label="Source health check",
                            description="Build a source map for prices, BCTC, news, macro and cache fallback.",
                            input_schema=_object_schema({"sources": {"type": "array"}, "required_fields": {"type": "array"}}),
                            output_schema=_object_schema({"source_map": {"type": "array"}, "fallback_order": {"type": "array"}}),
                            risk_level="medium",
                        ),
                    ),
                ),
                ProLabProviderDefinition(
                    provider_id="export_lab",
                    label="Export Lab",
                    category="developer_tools",
                    description="Export a strategy artifact into code, markdown checklist or execution-plan skeleton.",
                    enabled=True,
                    guardrails=(
                        "Exported code is a draft and should be reviewed before running.",
                        "No live broker credentials are embedded in exports.",
                    ),
                    commands=(
                        ProLabCommandDefinition(
                            command_id="strategy_code_export",
                            label="Strategy code export",
                            description="Generate a Python/Pine-style strategy skeleton and markdown runbook.",
                            input_schema=_object_schema({"target": {"type": "string"}, "include_alerts": {"type": "boolean"}}),
                            output_schema=_object_schema({"files": {"type": "array"}, "runbook": {"type": "array"}}),
                            risk_level="medium",
                        ),
                    ),
                ),
                ProLabProviderDefinition(
                    provider_id="journal_lab",
                    label="Journal Lab",
                    category="personal_execution",
                    description="Review a personal paper/live journal for rule breaks, drawdown and process drift.",
                    enabled=True,
                    guardrails=(
                        "Journal review is for process improvement and personal accountability.",
                        "It should flag deviations from the plan before scaling a strategy.",
                    ),
                    commands=(
                        ProLabCommandDefinition(
                            command_id="shadow_account_review",
                            label="Shadow account review",
                            description="Score paper/live journal discipline against planned rules and risk limits.",
                            input_schema=_object_schema(
                                {
                                    "journal_text": {"type": "string"},
                                    "max_daily_loss_pct": {"type": "number"},
                                    "max_rule_breaks": {"type": "number"},
                                }
                            ),
                            output_schema=_object_schema({"discipline_score": {"type": "number"}, "rule_breaks": {"type": "array"}}),
                            risk_level="critical",
                        ),
                    ),
                ),
                ProLabProviderDefinition(
                    provider_id="report_builder",
                    label="Report Builder",
                    category="reporting",
                    description="Transform experiment outputs into structured report sections with caveats and sources.",
                    enabled=True,
                    guardrails=("Every report section must carry caveats and freshness metadata.",),
                    commands=(
                        ProLabCommandDefinition(
                            command_id="research_memo",
                            label="Research memo",
                            description="Create a structured research memo shell from the selected blueprint.",
                            input_schema=_object_schema({"memo_focus": {"type": "string"}}),
                            output_schema=_object_schema({"report_sections": {"type": "array"}}),
                            risk_level="medium",
                        ),
                    ),
                ),
                ProLabProviderDefinition(
                    provider_id="private_auto_copy_trading",
                    label="Private Auto / Copy Trading",
                    category="private_controls",
                    description=(
                        "Private-only paper/control-plane module for personal automation design, copy-mapping simulation "
                        "and kill-switch review. It does not place live orders."
                    ),
                    enabled=True,
                    guardrails=(
                        "Private/internal only; never exposed as public recommendation or signal feed.",
                        "No broker order execution in this MVP.",
                        "Requires manual review, paper mode and kill-switch discipline before any real integration.",
                    ),
                    commands=(
                        ProLabCommandDefinition(
                            command_id="paper_auto_trading_plan",
                            label="Paper auto-trading plan",
                            description="Draft a paper-only automation control plan with limits, alerts and stop rules.",
                            input_schema=_object_schema(
                                {
                                    "strategy_brief": {"type": "string"},
                                    "max_daily_loss_pct": {"type": "number"},
                                    "max_position_pct": {"type": "number"},
                                }
                            ),
                            output_schema=_object_schema({"controls": {"type": "array"}, "runbook": {"type": "array"}}),
                            risk_level="critical",
                            private_only=True,
                        ),
                        ProLabCommandDefinition(
                            command_id="copy_trading_mapping_review",
                            label="Copy-trading mapping review",
                            description="Review how a source portfolio would map into a smaller personal risk budget.",
                            input_schema=_object_schema(
                                {
                                    "source_style": {"type": "string"},
                                    "personal_risk_budget_pct": {"type": "number"},
                                    "excluded_assets": {"type": "array"},
                                }
                            ),
                            output_schema=_object_schema({"mapping_checks": {"type": "array"}, "blockers": {"type": "array"}}),
                            risk_level="critical",
                            private_only=True,
                        ),
                    ),
                ),
            )
        }

    def list(self, *, include_private: bool = False) -> list[ProLabProviderDefinition]:
        providers = []
        for provider in self._providers.values():
            commands = tuple(command for command in provider.commands if include_private or not command.private_only)
            if commands:
                providers.append(
                    ProLabProviderDefinition(
                        provider_id=provider.provider_id,
                        label=provider.label,
                        category=provider.category,
                        description=provider.description,
                        enabled=provider.enabled,
                        commands=commands,
                        guardrails=provider.guardrails,
                    )
                )
        return providers

    def get_command(self, *, provider_id: str, command_id: str, include_private: bool = False) -> tuple[ProLabProviderDefinition, ProLabCommandDefinition]:
        provider = self._providers.get(provider_id)
        if provider is None or not provider.enabled:
            raise ValueError("Provider không tồn tại hoặc đang bị tắt.")
        command = next((item for item in provider.commands if item.command_id == command_id), None)
        if command is None:
            raise ValueError("Command không tồn tại trong provider này.")
        if command.private_only and not include_private:
            raise PermissionError("Command này chỉ dành cho private/internal Pro Lab.")
        return provider, command

    def execute(
        self,
        *,
        provider_id: str,
        command_id: str,
        input_payload: dict[str, object],
        blueprint: ProLabBlueprint | None,
        include_private: bool = False,
    ) -> ProLabProviderResult:
        provider, command = self.get_command(provider_id=provider_id, command_id=command_id, include_private=include_private)
        if provider.provider_id == "scenario_lab":
            return self._scenario_result(command_id=command.command_id, input_payload=input_payload, blueprint=blueprint)
        if provider.provider_id == "strategy_copilot":
            return self._strategy_copilot_result(input_payload=input_payload, blueprint=blueprint)
        if provider.provider_id == "swarm_committee":
            return self._swarm_committee_result(input_payload=input_payload, blueprint=blueprint)
        if provider.provider_id == "backtest_lab":
            return self._backtest_result(input_payload=input_payload, blueprint=blueprint)
        if provider.provider_id == "validation_lab":
            return self._validation_result(input_payload=input_payload, blueprint=blueprint)
        if provider.provider_id == "optimizer_lab":
            return self._optimizer_result(input_payload=input_payload, blueprint=blueprint)
        if provider.provider_id == "data_router":
            return self._data_router_result(input_payload=input_payload, blueprint=blueprint)
        if provider.provider_id == "export_lab":
            return self._export_result(input_payload=input_payload, blueprint=blueprint)
        if provider.provider_id == "journal_lab":
            return self._journal_result(input_payload=input_payload, blueprint=blueprint)
        if provider.provider_id == "report_builder":
            return self._report_result(input_payload=input_payload, blueprint=blueprint)
        if provider.provider_id == "private_auto_copy_trading":
            return self._private_trading_result(command_id=command.command_id, input_payload=input_payload, blueprint=blueprint)
        raise ValueError("Provider chưa có executor.")

    def _base_freshness(self) -> dict[str, object]:
        return {"source": "pro_lab_sandbox", "as_of": _now(), "stale": False}

    def _strategy_copilot_result(
        self,
        *,
        input_payload: dict[str, object],
        blueprint: ProLabBlueprint | None,
    ) -> ProLabProviderResult:
        idea = str(input_payload.get("idea") or blueprint.objective if blueprint else input_payload.get("idea") or "").strip()
        market = str(input_payload.get("market") or "Vietnam equities").strip()
        horizon = str(input_payload.get("horizon") or blueprint.rebalance_frequency if blueprint else input_payload.get("horizon") or "monthly").strip()
        universe = list(blueprint.asset_universe) if blueprint else ["FPT", "VCB", "MWG"]
        risk_budget = input_payload.get("risk_budget_pct") or 2
        return ProLabProviderResult(
            status="completed",
            progress_pct=100,
            logs=(
                {"level": "info", "message": "Parsed natural-language strategy idea.", "at": _now()},
                {"level": "warning", "message": "Draft requires scenario, backtest and risk review before use.", "at": _now()},
            ),
            safety_flags=("research_hypothesis_only", "validation_required", "no_trade_instruction"),
            data_freshness=self._base_freshness(),
            output_payload={
                "strategy_draft": {
                    "idea": idea or "Quality rotation with benchmark-aware risk controls.",
                    "market": market,
                    "universe": universe,
                    "signal_stack": [
                        "Quality/fundamental filter",
                        "Momentum confirmation",
                        "Drawdown and concentration control",
                    ],
                    "risk_budget_pct": risk_budget,
                    "cadence": horizon,
                },
                "validation_queue": [
                    "Check data coverage and survivorship bias.",
                    "Run scenario stress for FX/rate sensitivity.",
                    "Run benchmark sandbox with transaction-cost assumption.",
                    "Ask swarm committee to challenge overfit and execution assumptions.",
                ],
                "notebook_sections": [
                    {"title": "Strategy draft", "body": f"{market}: {idea or 'research idea'}"},
                    {"title": "Validation queue", "body": "Scenario -> Backtest -> Swarm review -> Memo export."},
                ],
                "caveats": ["This draft is not a buy/sell recommendation."],
            },
        )

    def _swarm_committee_result(
        self,
        *,
        input_payload: dict[str, object],
        blueprint: ProLabBlueprint | None,
    ) -> ProLabProviderResult:
        focus = str(input_payload.get("review_focus") or "overfit, risk and execution realism").strip()
        depth = str(input_payload.get("validation_depth") or "standard").strip()
        name = blueprint.name if blueprint else "selected strategy"
        role_memos = [
            {"role": "Strategist", "memo": f"Clarify why {name} should work across regimes before expanding the universe."},
            {"role": "Quant", "memo": "Require walk-forward windows, benchmark gap, drawdown and turnover review."},
            {"role": "Risk", "memo": "Check concentration, liquidity, stop rules and scenario sensitivity."},
            {"role": "Execution", "memo": "Separate signal logic from order/execution assumptions; no live execution in MVP."},
        ]
        return ProLabProviderResult(
            status="needs_review",
            progress_pct=100,
            logs=(
                {"level": "info", "message": "Built committee role memos.", "at": _now()},
                {"level": "warning", "message": "Committee output requires human sign-off.", "at": _now()},
            ),
            safety_flags=("human_signoff_required", "committee_not_advice", "execution_review_required"),
            data_freshness=self._base_freshness(),
            output_payload={
                "role_memos": role_memos,
                "signoff_checklist": [
                    f"Review focus: {focus}.",
                    f"Validation depth: {depth}.",
                    "No unresolved data-quality warnings.",
                    "Backtest assumptions, costs and benchmark are documented.",
                    "Risk controls are explicit and auditable.",
                ],
                "notebook_sections": [
                    {"title": "Committee summary", "body": f"{len(role_memos)} roles reviewed {name}."},
                    {"title": "Required sign-off", "body": "Resolve checklist items before treating this as a validated research artifact."},
                ],
                "caveats": ["Swarm review is structured critique, not personalized financial advice."],
            },
        )

    def _scenario_result(
        self,
        *,
        command_id: str,
        input_payload: dict[str, object],
        blueprint: ProLabBlueprint | None,
    ) -> ProLabProviderResult:
        asset_count = len(blueprint.asset_universe) if blueprint else 0
        return ProLabProviderResult(
            status="completed",
            progress_pct=100,
            logs=(
                {"level": "info", "message": "Loaded scenario command.", "at": _now()},
                {"level": "warning", "message": "Output is sensitivity analysis, not a forecast.", "at": _now()},
            ),
            safety_flags=("not_forecast", "review_concentration", "manual_interpretation_required"),
            data_freshness=self._base_freshness(),
            output_payload={
                "notebook_sections": [
                    {"title": "Scenario setup", "body": f"{command_id} on {asset_count} blueprint assets."},
                    {"title": "So what", "body": "Review which assumption changes the thesis most before changing the portfolio."},
                    {"title": "Now what", "body": "Compare against benchmark and concentration limits before any action."},
                ],
                "caveats": ["Scenario analysis does not predict market direction."],
            },
        )

    def _backtest_result(self, *, input_payload: dict[str, object], blueprint: ProLabBlueprint | None) -> ProLabProviderResult:
        asset_count = max(len(blueprint.asset_universe) if blueprint else 1, 1)
        return ProLabProviderResult(
            status="completed",
            progress_pct=100,
            logs=(
                {"level": "info", "message": "Built benchmark sandbox inputs.", "at": _now()},
                {"level": "warning", "message": "Execution realism is simplified in MVP.", "at": _now()},
            ),
            safety_flags=("backtest_not_prediction", "overfit_review_required", "execution_assumption_simplified"),
            data_freshness=self._base_freshness(),
            output_payload={
                "metrics": {
                    "asset_count": asset_count,
                    "sandbox_relative_gap_pct": round(min(asset_count * 0.8, 6.0), 2),
                    "initial_capital": input_payload.get("initial_capital"),
                },
                "notebook_sections": [
                    {"title": "Setup", "body": f"Benchmark sandbox for {blueprint.benchmark if blueprint else 'n/a'}."},
                    {"title": "Read this first", "body": "Backtest quality depends on data, assumptions, costs and bias controls."},
                ],
                "caveats": ["Historical sandbox output is not a performance promise."],
            },
        )

    def _validation_result(self, *, input_payload: dict[str, object], blueprint: ProLabBlueprint | None) -> ProLabProviderResult:
        window = input_payload.get("window_months") or 6
        cost_bps = input_payload.get("cost_bps") or 20
        simulations = input_payload.get("simulations") or 1000
        return ProLabProviderResult(
            status="needs_review",
            progress_pct=100,
            logs=(
                {"level": "info", "message": "Prepared walk-forward and Monte Carlo validation suite.", "at": _now()},
                {"level": "warning", "message": "Validation suite is a checklist until connected to the full execution simulator.", "at": _now()},
            ),
            safety_flags=("validation_required", "cost_sensitivity_required", "overfit_review_required"),
            data_freshness=self._base_freshness(),
            output_payload={
                "validation_suite": [
                    {"check": "Walk-forward split", "setting": f"{window} month rolling validation"},
                    {"check": "Transaction cost sensitivity", "setting": f"{cost_bps} bps per turnover event"},
                    {"check": "Monte Carlo trade order", "setting": f"{simulations} randomized paths"},
                    {"check": "Benchmark persistence", "setting": "Compare win rate by regime, not only full-period CAGR"},
                ],
                "fail_conditions": [
                    "Sharpe collapses after realistic transaction costs.",
                    "Max drawdown exceeds personal risk budget.",
                    "Performance only exists in one market regime.",
                    "Turnover cannot be executed with available liquidity.",
                ],
                "notebook_sections": [
                    {"title": "Validation suite", "body": "Walk-forward, Monte Carlo, cost and regime checks prepared."},
                    {"title": "Blockers", "body": "Treat fail conditions as blockers before scaling the strategy."},
                ],
                "caveats": ["Connect real fills and price history before treating this as a completed validation."],
            },
        )

    def _optimizer_result(self, *, input_payload: dict[str, object], blueprint: ProLabBlueprint | None) -> ProLabProviderResult:
        universe = list(blueprint.asset_universe) if blueprint else ["FPT", "VCB", "MWG"]
        max_weight = float(input_payload.get("max_weight_pct") or 35)
        method = str(input_payload.get("method") or "risk_parity").strip()
        raw_weight = min(max_weight, round(100 / max(len(universe), 1), 2))
        allocation = [{"ticker": ticker, "target_weight_pct": raw_weight, "role": "core" if index == 0 else "satellite"} for index, ticker in enumerate(universe)]
        residual = round(100 - sum(item["target_weight_pct"] for item in allocation), 2)
        if allocation and abs(residual) > 0:
            allocation[-1]["target_weight_pct"] = round(allocation[-1]["target_weight_pct"] + residual, 2)
        return ProLabProviderResult(
            status="completed",
            progress_pct=100,
            logs=({"level": "info", "message": "Generated allocation draft from blueprint universe.", "at": _now()},),
            safety_flags=("allocation_draft", "liquidity_check_required", "rebalance_review_required"),
            data_freshness=self._base_freshness(),
            output_payload={
                "optimizer": {"method": method, "max_weight_pct": max_weight, "target_volatility_pct": input_payload.get("target_volatility_pct")},
                "allocation": allocation,
                "constraint_checks": [
                    "No ticker exceeds max weight.",
                    "Review liquidity before accepting target weights.",
                    "Review sector/theme concentration manually.",
                    "Set rebalance band before implementation.",
                ],
                "notebook_sections": [
                    {"title": "Allocation draft", "body": f"{method} draft for {len(universe)} tickers."},
                    {"title": "Constraint checks", "body": "Max weight, liquidity and concentration checks generated."},
                ],
                "caveats": ["Expected return and covariance assumptions are not yet calibrated from live data."],
            },
        )

    def _data_router_result(self, *, input_payload: dict[str, object], blueprint: ProLabBlueprint | None) -> ProLabProviderResult:
        required = input_payload.get("required_fields") or ["price", "volume", "financials", "news", "macro"]
        source_map = [
            {"domain": "prices", "primary": "local_cache", "fallback": "provider_live", "status": "ready"},
            {"domain": "financials", "primary": "vnstock_cache", "fallback": "json_import", "status": "ready"},
            {"domain": "news", "primary": "rss_pipeline", "fallback": "tavily_search", "status": "ready"},
            {"domain": "macro", "primary": "curated_cache", "fallback": "manual_import", "status": "partial"},
        ]
        return ProLabProviderResult(
            status="completed",
            progress_pct=100,
            logs=({"level": "info", "message": "Built data source map and fallback order.", "at": _now()},),
            safety_flags=("data_quality_visible", "fallback_order_declared"),
            data_freshness=self._base_freshness(),
            output_payload={
                "required_fields": required,
                "source_map": source_map,
                "fallback_order": ["local_cache", "provider_live", "json_import", "manual_import"],
                "notebook_sections": [
                    {"title": "Data readiness", "body": "Sources and fallbacks are declared before running experiments."},
                    {"title": "Partial areas", "body": "Macro data may require manual/imported confirmation."},
                ],
                "caveats": ["A ready source map does not guarantee every ticker has complete history."],
            },
        )

    def _export_result(self, *, input_payload: dict[str, object], blueprint: ProLabBlueprint | None) -> ProLabProviderResult:
        target = str(input_payload.get("target") or "python").strip().lower()
        universe = list(blueprint.asset_universe) if blueprint else ["FPT", "VCB", "MWG"]
        files = [
            {
                "filename": "strategy_blueprint.md",
                "language": "markdown",
                "content": f"# {blueprint.name if blueprint else 'Strategy Blueprint'}\n\nUniverse: {', '.join(universe)}\n\nReview scenario, backtest and journal before scaling.",
            },
            {
                "filename": "strategy_skeleton.py" if target != "pine" else "strategy_skeleton.pine",
                "language": "python" if target != "pine" else "pine",
                "content": _strategy_code_template(target=target, universe=universe),
            },
        ]
        return ProLabProviderResult(
            status="completed",
            progress_pct=100,
            logs=({"level": "info", "message": "Generated export artifacts.", "at": _now()},),
            safety_flags=("code_draft", "no_credentials", "review_before_run"),
            data_freshness=self._base_freshness(),
            output_payload={
                "files": files,
                "runbook": [
                    "Review generated rules.",
                    "Run validation lab.",
                    "Run paper/shadow journal for at least one cycle.",
                    "Keep broker credentials outside generated files.",
                ],
                "notebook_sections": [
                    {"title": "Export package", "body": f"Generated {len(files)} files for {target} workflow."},
                    {"title": "Runbook", "body": "Use export only after validation and journal review."},
                ],
                "caveats": ["Generated code is a starter skeleton, not production execution code."],
            },
        )

    def _journal_result(self, *, input_payload: dict[str, object], blueprint: ProLabBlueprint | None) -> ProLabProviderResult:
        journal = str(input_payload.get("journal_text") or "").strip()
        max_breaks = int(input_payload.get("max_rule_breaks") or 2)
        rule_breaks = []
        if "chase" in journal.lower() or "fomo" in journal.lower():
            rule_breaks.append("Detected possible chase/FOMO entry language.")
        if "oversize" in journal.lower() or "all in" in journal.lower():
            rule_breaks.append("Detected possible position sizing violation.")
        if not journal:
            rule_breaks.append("No journal text supplied; cannot verify process discipline.")
        score = max(0, 100 - len(rule_breaks) * 22 - (8 if len(rule_breaks) > max_breaks else 0))
        return ProLabProviderResult(
            status="needs_review" if rule_breaks else "completed",
            progress_pct=100,
            logs=({"level": "info", "message": "Reviewed journal text against risk-process rules.", "at": _now()},),
            safety_flags=("personal_journal", "discipline_review", "scale_only_after_review"),
            data_freshness=self._base_freshness(),
            output_payload={
                "discipline_score": score,
                "rule_breaks": rule_breaks,
                "review_prompts": [
                    "Entry matched the planned setup?",
                    "Position size respected max risk?",
                    "Exit plan was written before entry?",
                    "Did macro/news context change the thesis?",
                ],
                "notebook_sections": [
                    {"title": "Journal score", "body": f"Process discipline score: {score}/100."},
                    {"title": "Rule breaks", "body": "; ".join(rule_breaks) if rule_breaks else "No obvious rule break detected from supplied text."},
                ],
                "caveats": ["Journal NLP is heuristic until connected to structured trade logs."],
            },
        )

    def _report_result(self, *, input_payload: dict[str, object], blueprint: ProLabBlueprint | None) -> ProLabProviderResult:
        return ProLabProviderResult(
            status="completed",
            progress_pct=100,
            logs=({"level": "info", "message": "Generated report shell.", "at": _now()},),
            safety_flags=("report_requires_review",),
            data_freshness=self._base_freshness(),
            output_payload={
                "report_sections": [
                    {"type": "summary", "title": "Research question", "body": input_payload.get("memo_focus") or blueprint.objective if blueprint else "n/a"},
                    {"type": "caveat", "title": "Boundary", "body": "This memo is research support, not personalized financial advice."},
                ],
                "caveats": ["Review before external sharing."],
            },
        )

    def _private_trading_result(
        self,
        *,
        command_id: str,
        input_payload: dict[str, object],
        blueprint: ProLabBlueprint | None,
    ) -> ProLabProviderResult:
        if command_id == "copy_trading_mapping_review":
            body = {
                "mapping_checks": [
                    "Normalize position size to personal risk budget.",
                    "Block assets outside the approved universe.",
                    "Require manual confirmation before any execution integration.",
                ],
                "blockers": [
                    "No live broker connector is enabled.",
                    "No suitability or liquidity review has been completed.",
                ],
            }
        else:
            body = {
                "controls": [
                    "Paper mode only.",
                    "Daily loss limit must trigger kill switch.",
                    "Max position size must be enforced before signal evaluation.",
                    "Manual review required before promoting any rule.",
                ],
                "runbook": [
                    "Start with paper ledger.",
                    "Log every simulated signal and skipped signal.",
                    "Review drawdown and rule drift weekly.",
                ],
            }
        return ProLabProviderResult(
            status="needs_review",
            progress_pct=100,
            logs=(
                {"level": "warning", "message": "Private auto/copy trading is control-plane only in this MVP.", "at": _now()},
                {"level": "warning", "message": "No order execution was attempted.", "at": _now()},
            ),
            safety_flags=("private_only", "no_live_orders", "manual_review_required", "kill_switch_required"),
            data_freshness=self._base_freshness(),
            output_payload={
                **body,
                "blueprint": blueprint.name if blueprint else None,
                "caveats": [
                    "This is not a recommendation to buy or sell.",
                    "Live auto-trading requires separate broker, compliance, suitability and kill-switch implementation.",
                ],
            },
        )
