from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Literal
import uuid

from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.internal_ops.application.policy import (
    PolicyDeniedError,
    PolicyEngine,
    PurposeGrant,
    utc_now,
)
from risk_dashboard.modules.internal_ops.application.verifier import Verifier
from risk_dashboard.modules.internal_ops.domain.contracts import (
    EvidenceBatch,
    EvidenceItem,
    EvidenceRef,
    InvestigationRequest,
    OpsInvestigationReport,
)
from risk_dashboard.modules.internal_ops.domain.tools import (
    InvestigationToolGrant,
    ToolRegistry,
)
from risk_dashboard.modules.internal_ops.application.synthesizer import (
    build_blocked_report,
    synthesize_findings_and_hypotheses,
)

logger = logging.getLogger(__name__)


class InvestigationService:
    def __init__(
        self,
        adapters: dict[str, Any],
        verifier: Verifier | None = None,
        repository: Any | None = None,
    ) -> None:
        self._adapters = adapters
        self._verifier = verifier or Verifier()
        self._repo = repository

    def run_investigation(
        self,
        principal: AuthPrincipal,
        request: InvestigationRequest,
    ) -> OpsInvestigationReport:
        now_iso = utc_now().isoformat()
        inv_id, rep_id = f"inv-{uuid.uuid4().hex[:10]}", f"rep-{uuid.uuid4().hex[:10]}"

        # 1. Authorize PurposeGrant
        try:
            grant = PolicyEngine.create_grant(principal=principal, purpose=request.purpose)
        except PolicyDeniedError as exc:
            report = build_blocked_report(rep_id, inv_id, request, f"Policy blocked: {exc}", now_iso, now_iso)
            if self._repo:
                self._repo.record_audit(principal.account_id, "policy_blocked", request.purpose, inv_id)
            return report

        # 2. Gather Evidence
        all_items: list[EvidenceItem] = []
        limitations: list[str] = []
        status: Literal["draft", "incomplete", "policy_blocked", "failed"] = "draft"

        for ref in request.resource_refs:
            batch = self._fetch_by_ref(grant, ref, inv_id=inv_id)
            if batch.status == "source_unavailable":
                limitations.append(f"Source {ref.source_module} unavailable for {ref.resource_id}")
                status = "incomplete"
            all_items.extend(batch.items)

        if not request.resource_refs:
            auto_batch, auto_lims = self._gather_domain_evidence(grant, request.investigation_type, inv_id=inv_id)
            all_items.extend(auto_batch)
            limitations.extend(auto_lims)
            if auto_lims:
                status = "incomplete"

        capped_items = all_items[: request.max_evidence_items]

        # 3. Formulate Deterministic Findings & Hypotheses
        raw_f, raw_h, recs, surfaces = synthesize_findings_and_hypotheses(request, capped_items)

        # 4. Deterministic Citation Verification
        verified_f, dropped = self._verifier.verify_citations(raw_f, tuple(capped_items))
        if dropped:
            limitations.extend(dropped)

        # 5. Build Report
        report = OpsInvestigationReport(
            report_id=rep_id,
            investigation_id=inv_id,
            status=status,
            purpose=request.purpose,
            severity="medium" if verified_f else "info",
            time_from=request.time_from,
            time_to=request.time_to,
            verified_findings=verified_f,
            hypotheses=raw_h,
            recommendations=recs,
            impacted_surfaces=surfaces,
            limitations=tuple(limitations),
            access_expires_at=grant.expires_at,
            created_at=now_iso,
        )

        # 6. Check Forbidden Intent
        if self._verifier.check_forbidden_intent(report) == "policy_blocked":
            report = build_blocked_report(
                rep_id, inv_id, request, "Report blocked by forbidden intent verifier.", grant.expires_at, now_iso
            )

        if self._repo:
            self._repo.save_investigation(inv_id, principal.account_id, request, report, capped_items)
            self._repo.record_audit(principal.account_id, "investigation_completed", request.purpose, inv_id)

        return report

    def _exec_tool(self, tool_id: str, inv_id: str, grant: PurposeGrant, params: dict[str, Any]) -> Any:
        tg = InvestigationToolGrant(
            grant_id=f"tg-{uuid.uuid4().hex[:8]}",
            investigation_id=inv_id,
            tool_id=tool_id,
            purpose=grant.purpose,
            expires_at=grant.expires_at,
            max_calls=50,
        )
        return ToolRegistry.execute(tool_id, tg, grant, self._adapters, params)

    def _fetch_by_ref(self, grant: PurposeGrant, ref: EvidenceRef, inv_id: str = "inv-ops") -> EvidenceBatch:
        tool_map = {
            "analytics_monitoring": ("ops.get_kpi_slice@1.0.0", {"kpi_name": ref.resource_id}),
            "trust_safety": ("ops.get_trust_case@1.0.0", {"surface": ref.resource_id}),
            "admin_cms": ("ops.get_content_context@1.0.0", {"content_id": ref.resource_id}),
            "agentic_core": ("ops.get_run_trace@1.0.0", {}),
        }
        mod = ref.source_module
        mapping = tool_map.get(mod)
        if mapping:
            tool_id, params = mapping
            try:
                return self._exec_tool(tool_id, inv_id, grant, params)
            except Exception as exc:
                logger.warning("Adapter fetch failed for %s (%s): %s", tool_id, ref.resource_id, exc)
        return EvidenceBatch(items=(), source_module=mod, fetched_at=utc_now().isoformat(), status="source_unavailable")

    def _gather_domain_evidence(
        self, grant: PurposeGrant, inv_type: str, inv_id: str = "inv-ops"
    ) -> tuple[list[EvidenceItem], list[str]]:
        items: list[EvidenceItem] = []
        limitations: list[str] = []
        plan: list[str] = []
        if inv_type in ("incident", "data_freshness") and "analytics_monitoring" in grant.allowed_modules and "analytics" in self._adapters:
            plan.extend(["ops.get_source_health@1.0.0", "ops.get_alert_context@1.0.0"])
        if inv_type == "incident" and "trust_safety" in grant.allowed_modules and "trust_safety" in self._adapters:
            plan.append("ops.get_trust_case@1.0.0")
        if inv_type == "content_qa" and "admin_cms" in grant.allowed_modules and "admin_cms" in self._adapters:
            plan.append("ops.get_content_context@1.0.0")

        for tid in plan:
            try:
                items.extend(self._exec_tool(tid, inv_id, grant, {}).items)
            except Exception as exc:
                logger.warning("Gathering tool %s failed: %s", tid, exc)
                limitations.append(f"Source error ({tid}): {exc}")

        if inv_type in ("run_failure", "eval_regression"):
            limitations.append("Agentic core run traces disabled until AC6 freeze.")
        return items, limitations


