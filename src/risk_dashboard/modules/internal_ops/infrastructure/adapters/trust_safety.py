from __future__ import annotations

from datetime import datetime, timezone

from risk_dashboard.modules.internal_ops.application.policy import (
    PolicyDeniedError,
    PolicyEngine,
    PurposeGrant,
)
from risk_dashboard.modules.internal_ops.application.redaction import RedactionEngine
from risk_dashboard.modules.internal_ops.domain.contracts import (
    EvidenceBatch,
    EvidenceItem,
    EvidenceRef,
)
from risk_dashboard.modules.trust_safety.application.services import (
    ListTrustIncidents,
    ListTrustSafetyAudit,
)
from risk_dashboard.modules.trust_safety.infrastructure.repositories.sqlite import (
    SqliteTrustSafetyRepository,
)

TRUST_AUDIT_ALLOWLIST = {"surface", "risk_class", "severity", "action", "as_of", "details"}
TRUST_INCIDENT_ALLOWLIST = {
    "incident_id",
    "surface",
    "severity",
    "status",
    "opened_at",
    "title",
    "summary",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TrustSafetyAdapter:
    """Direct in-process adapter to Trust & Safety services. Zero HTTP loopback."""

    def __init__(
        self,
        audit_service: ListTrustSafetyAudit | None = None,
        incidents_service: ListTrustIncidents | None = None,
    ) -> None:
        repo = SqliteTrustSafetyRepository()
        self._audit_svc = audit_service or ListTrustSafetyAudit(repo=repo)
        self._incidents_svc = incidents_service or ListTrustIncidents(repo=repo)

    def get_trust_case(
        self,
        grant: PurposeGrant,
        surface: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> EvidenceBatch:
        PolicyEngine.authorize_tool_call(grant, "ops.get_trust_case@1.0.0", "trust_safety")

        # Specific purpose requirement: purpose must relate to safety review or incident triage
        p_lower = grant.purpose.lower()
        if not any(k in p_lower for k in ("safety", "incident", "triage", "review", "audit", "investigat")):
            raise PolicyDeniedError("Trust Safety access requires purpose oriented toward safety/incident review.")

        capped_limit = min(max(limit, 1), 500)
        incidents = self._incidents_svc.execute(surface=surface, status=status, limit=capped_limit)
        audits = self._audit_svc.execute(surface=surface, limit=capped_limit)

        items: list[EvidenceItem] = []
        now_iso = _utc_now_iso()

        for inc in incidents:
            raw_dict = inc.model_dump() if hasattr(inc, "model_dump") else dict(inc)
            clean_fields, reds = RedactionEngine.filter_and_redact_dict(raw_dict, TRUST_INCIDENT_ALLOWLIST)
            ref = EvidenceRef(
                source_module="trust_safety",
                resource_type="trust_incident",
                resource_id=str(clean_fields.get("incident_id", "incident")),
                observed_at=clean_fields.get("opened_at", now_iso),
            )
            items.append(
                EvidenceItem(
                    ref=ref,
                    classification="restricted_redacted",
                    fields=clean_fields,
                    redactions=tuple(reds),
                )
            )

        for aud in audits:
            raw_dict = aud.model_dump() if hasattr(aud, "model_dump") else dict(aud)
            clean_fields, reds = RedactionEngine.filter_and_redact_dict(raw_dict, TRUST_AUDIT_ALLOWLIST)
            ref = EvidenceRef(
                source_module="trust_safety",
                resource_type="trust_audit",
                resource_id=f"audit-{clean_fields.get('surface', 'all')}",
                observed_at=clean_fields.get("as_of", now_iso),
            )
            items.append(
                EvidenceItem(
                    ref=ref,
                    classification="restricted_redacted",
                    fields=clean_fields,
                    redactions=tuple(reds),
                )
            )

        return EvidenceBatch(
            items=tuple(items),
            source_module="trust_safety",
            fetched_at=now_iso,
            status="available",
        )

