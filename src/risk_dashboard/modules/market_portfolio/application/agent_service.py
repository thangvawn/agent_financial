from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
import uuid
from typing import Any

from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.market_portfolio.application.agent_tools import (
    explain_fill,
    get_exposure,
    get_market_snapshot,
    run_scenario,
)
from risk_dashboard.modules.market_portfolio.application.reviewers import (
    EvidenceReviewer,
    NumericReviewer,
    SafetyReviewer,
)
from risk_dashboard.modules.market_portfolio.application.skills import (
    ALL_SKILLS,
    MARKET_CONTEXT_EXPLAINER_SKILL,
    PORTFOLIO_EXPOSURE_REVIEW_SKILL,
    PORTFOLIO_PAPER_FILL_EXPLAINER_SKILL,
    PORTFOLIO_SCENARIO_WALKTHROUGH_SKILL,
)

from risk_dashboard.modules.market_portfolio.domain.ports import ToolContext
from risk_dashboard.modules.market_portfolio.infrastructure.artifact_repository import ArtifactRepository
from risk_dashboard.modules.market_portfolio.schemas.agent_api import (
    EvidenceRefV1,
    PortfolioReviewArtifactV1,
    StartPortfolioReviewRequestV1,
    StartPortfolioReviewResponseV1,
)
from risk_dashboard.modules.market_portfolio.schemas.agent_tools import (
    ExplainFillInputV1,
    FreshnessStampV1,
    GetExposureInputV1,
    GetMarketSnapshotInputV1,
    PriceShockV1,
)
from risk_dashboard.platform.ai_runtime.contracts import ModelMessage, ModelSettings, ModelTask
from risk_dashboard.platform.ai_runtime.factory import get_default_provider
from risk_dashboard.platform.ai_runtime.provider import LLMProvider

logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class MarketPortfolioAgentService:
    def __init__(
        self,
        artifact_repo: ArtifactRepository | None = None,
        provider: LLMProvider | None = None,
    ) -> None:
        self.artifact_repo = artifact_repo or ArtifactRepository()
        self._provider = provider
        self.numeric_reviewer = NumericReviewer()
        self.evidence_reviewer = EvidenceReviewer()
        self.safety_reviewer = SafetyReviewer()

    def _get_provider(self) -> LLMProvider:
        if self._provider is not None:
            return self._provider
        return get_default_provider()

    async def start_review(
        self,
        request: StartPortfolioReviewRequestV1,
        principal: AuthPrincipal,
    ) -> StartPortfolioReviewResponseV1:
        # 1. Check idempotency
        cached = self.artifact_repo.get_by_idempotency_key(principal.account_id, request.idempotency_key)
        if cached:
            return StartPortfolioReviewResponseV1(
                schema_version="1.0.0",
                run_id=f"run-{cached.artifact_id}",
                artifact=cached,
            )

        run_id = f"run-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).replace(microsecond=0)
        now_iso = now.isoformat()
        ctx = ToolContext(principal=principal, run_id=run_id, now_iso=now_iso)

        # 2. Dispatch review type & run deterministic tools
        observed_facts: list[str] = []
        calculations: dict[str, Any] = {}
        evidence_list: list[EvidenceRefV1] = []
        assumptions: tuple[PriceShockV1, ...] = ()
        limitations: list[str] = ["Educational paper trading simulation only. No real execution."]
        freshness: FreshnessStampV1
        snapshot_version: str
        skill = ALL_SKILLS[MARKET_CONTEXT_EXPLAINER_SKILL.skill_id]

        if request.review_type == "market_context":
            skill = MARKET_CONTEXT_EXPLAINER_SKILL
            m_res = await get_market_snapshot(GetMarketSnapshotInputV1(), ctx)
            if not m_res.indices and not m_res.quotes:
                raise ValueError("Market data unavailable: market feed returned no index or quote data.")
            freshness = m_res.freshness
            snapshot_version = freshness.as_of
            for idx in m_res.indices[:3]:
                sym = idx.get("symbol")
                close = idx.get("close")
                pct = idx.get("change_pct")
                if sym and close is not None and pct is not None:
                    observed_facts.append(f"Chỉ số {sym}: Đóng cửa {close}, biến động {pct}%.")
                    calculations[f"index_{sym}_change_pct"] = float(pct)
            evidence_list.append(EvidenceRefV1(

                tool_call_id=f"call-{uuid.uuid4().hex[:8]}",
                tool_name="market.get_snapshot.v1",
                output_schema_version="1.0.0",
                resource_id="VN",
                as_of=freshness.as_of,
            ))

        elif request.review_type == "exposure":
            skill = PORTFOLIO_EXPOSURE_REVIEW_SKILL
            exp_res = await get_exposure(GetExposureInputV1(portfolio_id=request.portfolio_id), ctx)
            freshness = exp_res.freshness
            snapshot_version = exp_res.snapshot_version
            observed_facts.append(f"Tỷ trọng đầu tư: {exp_res.invested_pct}%, Tiền mặt: {exp_res.cash_pct}%.")
            if exp_res.largest_position_pct is not None:
                observed_facts.append(f"Vị thế lớn nhất: {exp_res.largest_position_pct}%, Top 3: {exp_res.top3_concentration_pct}%.")
            if exp_res.hhi is not None:
                observed_facts.append(f"Chỉ số tập trung Herfindahl-Hirschman (HHI): {exp_res.hhi:.4f}.")
            calculations["invested_pct"] = exp_res.invested_pct
            calculations["cash_pct"] = exp_res.cash_pct
            calculations["largest_position_pct"] = exp_res.largest_position_pct
            calculations["top3_concentration_pct"] = exp_res.top3_concentration_pct
            calculations["hhi"] = exp_res.hhi
            for s, w in exp_res.weights_pct.items():
                calculations[f"weight_{s}"] = w
            limitations.extend(exp_res.limitations)
            evidence_list.append(EvidenceRefV1(
                tool_call_id=f"call-{uuid.uuid4().hex[:8]}",
                tool_name="portfolio.get_exposure.v1",
                output_schema_version="1.0.0",
                resource_id=request.portfolio_id,
                as_of=freshness.as_of,
            ))

        elif request.review_type == "scenario":
            skill = PORTFOLIO_SCENARIO_WALKTHROUGH_SKILL
            if request.scenario is None:
                raise ValueError("Scenario input required for scenario review.")
            scen_res = await run_scenario(request.scenario, ctx)
            freshness = scen_res.freshness
            snapshot_version = scen_res.base_snapshot_version
            assumptions = scen_res.assumptions
            observed_facts.append(
                f"Tài sản ban đầu: {scen_res.base_equity.amount} {scen_res.base_equity.currency}, "
                f"Sau kịch bản sốc: {scen_res.scenario_equity.amount} {scen_res.scenario_equity.currency}."
            )
            observed_facts.append(
                f"Biến động PnL dự kiến: {scen_res.pnl_delta.amount} {scen_res.pnl_delta.currency} ({scen_res.pnl_delta_pct}%)."
            )
            calculations["base_equity"] = scen_res.base_equity.amount
            calculations["scenario_equity"] = scen_res.scenario_equity.amount
            calculations["pnl_delta"] = scen_res.pnl_delta.amount
            calculations["pnl_delta_pct"] = scen_res.pnl_delta_pct
            for sym, d_money in scen_res.position_deltas.items():
                calculations[f"delta_{sym}"] = d_money.amount
            limitations.extend(scen_res.limitations)
            evidence_list.append(EvidenceRefV1(
                tool_call_id=f"call-{uuid.uuid4().hex[:8]}",
                tool_name="portfolio.run_scenario.v1",
                output_schema_version="1.0.0",
                resource_id=request.portfolio_id,
                as_of=freshness.as_of,
            ))

        elif request.review_type == "fill":
            skill = PORTFOLIO_PAPER_FILL_EXPLAINER_SKILL
            if not request.order_id:
                raise ValueError("Order ID required for fill review.")
            fill_res = await explain_fill(ExplainFillInputV1(portfolio_id=request.portfolio_id, order_id=request.order_id), ctx)
            freshness = fill_res.freshness
            snapshot_version = freshness.as_of
            observed_facts.extend(fill_res.explanation_facts)
            calculations["filled_qty"] = fill_res.filled_quantity
            if fill_res.filled_price:
                calculations["filled_price"] = fill_res.filled_price.amount
            if fill_res.limit_price:
                calculations["limit_price"] = fill_res.limit_price.amount
            evidence_list.append(EvidenceRefV1(
                tool_call_id=f"call-{uuid.uuid4().hex[:8]}",
                tool_name="portfolio.explain_fill.v1",
                output_schema_version="1.0.0",
                resource_id=request.order_id,
                as_of=freshness.as_of,
            ))

        # 3. Evidence Reviewer check
        ev_decision = self.evidence_reviewer.review(evidence_list)
        if ev_decision.verdict == "reject":
            return StartPortfolioReviewResponseV1(
                schema_version="1.0.0",
                run_id=run_id,
                artifact=None,
                error_code="evidence_validation_failed",
            )

        # 4. LLM Generation via LLMProvider
        narrative: str | None = None
        narrative_status: str = "unavailable"
        review_status: str = "reviewed"

        user_content = (
            f"Review Type: {request.review_type}\n"
            f"Portfolio ID: {request.portfolio_id}\n"
            f"Paper Context: Educational simulated portfolio.\n"
            f"Observed Facts:\n" + "\n".join(f"- {f}" for f in observed_facts) + "\n"
            f"Calculations:\n" + "\n".join(f"- {k}: {v}" for k, v in calculations.items()) + "\n"
            "Task: Provide a concise educational summary explaining these exact facts and calculations. "
            "Never provide investment advice or buy/sell calls."
        )

        task = ModelTask(
            task_type="market_portfolio_review",
            system_instructions_ref=skill.skill_id,
            messages=(
                ModelMessage(role="system", content=skill.system_prompt),
                ModelMessage(role="user", content=user_content),
            ),
            settings=ModelSettings(temperature=0.2, response_format="text"),
            correlation_id=run_id,
        )

        try:
            provider = self._get_provider()
            res = await provider.generate(task)
            gen_text = res.text.strip()

            # 5. Run reviewers on generated narrative
            safety_decision = self.safety_reviewer.review(gen_text)
            numeric_decision = self.numeric_reviewer.review(gen_text, calculations)

            # 1-turn repair loop if repair requested
            if safety_decision.verdict == "repair" or numeric_decision.verdict == "repair":
                repair_reasons = list(safety_decision.violations) + list(numeric_decision.violations)
                repair_prompt = (
                    f"Bản nháp trước đó có các điểm cần điều chỉnh:\n"
                    + "\n".join(f"- {r}" for r in repair_reasons)
                    + "\nHãy viết lại bản phân tích ngắn gọn, nêu rõ đây là paper portfolio/mô phỏng giáo dục, "
                    + "chỉ dùng đúng các số liệu được cung cấp và tuyệt đối không đưa ra khuyến nghị mua bán."
                )
                repair_task = ModelTask(
                    task_type="market_portfolio_review_repair",
                    system_instructions_ref=skill.skill_id,
                    messages=(
                        ModelMessage(role="system", content=skill.system_prompt),
                        ModelMessage(role="user", content=user_content),
                        ModelMessage(role="assistant", content=gen_text),
                        ModelMessage(role="user", content=repair_prompt),
                    ),
                    settings=ModelSettings(temperature=0.1, response_format="text"),
                    correlation_id=run_id,
                )
                try:
                    repair_res = await provider.generate(repair_task)
                    repaired_text = repair_res.text.strip()
                    safety_decision = self.safety_reviewer.review(repaired_text)
                    numeric_decision = self.numeric_reviewer.review(repaired_text, calculations)
                    if safety_decision.verdict == "pass" and numeric_decision.verdict == "pass":
                        gen_text = repaired_text
                except Exception as repair_exc:
                    logger.warning("Repair loop generation failed: %s", repair_exc)

            if safety_decision.verdict == "pass" and numeric_decision.verdict == "pass":
                narrative = gen_text
                narrative_status = "generated"
                review_status = "reviewed"
            else:
                narrative = None
                narrative_status = "blocked"
                review_status = "rejected"
        except Exception as e:
            logger.warning("LLM generation failed for portfolio review: %s", e)
            narrative = None
            narrative_status = "unavailable"
            review_status = "reviewed"


        # 6. Build and store artifact
        artifact = PortfolioReviewArtifactV1(
            schema_version="1.0.0",
            artifact_id=f"art-{uuid.uuid4().hex[:12]}",
            account_id=principal.account_id,
            portfolio_id=request.portfolio_id,
            portfolio_kind="paper",
            snapshot_version=snapshot_version,
            review_type=request.review_type,
            observed_facts=tuple(observed_facts),
            calculations=calculations,
            scenario_assumptions=assumptions,
            narrative=narrative,
            narrative_status=narrative_status,
            evidence=tuple(evidence_list),
            limitations=tuple(limitations),
            freshness=freshness,
            review_status=review_status,
            created_at=now_iso,
            expires_at=(now + timedelta(hours=24)).isoformat(),
        )

        self.artifact_repo.save_artifact(artifact, request.idempotency_key)

        return StartPortfolioReviewResponseV1(
            schema_version="1.0.0",
            run_id=run_id,
            artifact=artifact,
        )

    def get_artifact(self, principal: AuthPrincipal, artifact_id: str) -> PortfolioReviewArtifactV1 | None:
        """Fetch artifact owned by principal; non-disclosing if non-existent or owned by another account."""
        return self.artifact_repo.get_artifact(principal.account_id, artifact_id)

