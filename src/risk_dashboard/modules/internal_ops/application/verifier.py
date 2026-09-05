from __future__ import annotations

import re
from typing import Literal

from risk_dashboard.modules.internal_ops.domain.contracts import (
    EvidenceItem,
    EvidenceRef,
    OpsInvestigationReport,
    VerifiedFinding,
)

FORBIDDEN_INTENT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(auto[-_ ]?publish|publish[-_ ]?content|force[-_ ]?publish)\b", re.IGNORECASE),
    re.compile(r"\b(close[-_ ]?incident|resolve[-_ ]?incident|reassign[-_ ]?incident)\b", re.IGNORECASE),
    re.compile(r"\b(change[-_ ]?prompt|change[-_ ]?model|change[-_ ]?flag|update[-_ ]?role|modify[-_ ]?config)\b", re.IGNORECASE),
    re.compile(r"\b(run[-_ ]?analytics[-_ ]?job|trigger[-_ ]?job|execute[-_ ]?job)\b", re.IGNORECASE),
]


class Verifier:
    @staticmethod
    def _ref_key(ref: EvidenceRef) -> tuple[str, str, str]:
        return (ref.source_module, ref.resource_type, ref.resource_id)

    @classmethod
    def verify_citations(
        cls,
        findings: tuple[VerifiedFinding, ...],
        evidence: tuple[EvidenceItem, ...],
    ) -> tuple[tuple[VerifiedFinding, ...], list[str]]:
        known_refs = {cls._ref_key(item.ref) for item in evidence}
        verified: list[VerifiedFinding] = []
        dropped: list[str] = []

        for finding in findings:
            valid_refs = [
                ref for ref in finding.evidence_refs
                if cls._ref_key(ref) in known_refs
            ]
            if not valid_refs:
                dropped.append(f"Finding dropped (no verified citations): {finding.statement[:60]}")
                continue
            verified.append(
                VerifiedFinding(
                    statement=finding.statement,
                    evidence_refs=tuple(valid_refs),
                )
            )
        return tuple(verified), dropped

    @classmethod
    def check_forbidden_intent(cls, report: OpsInvestigationReport) -> Literal["pass", "policy_blocked"]:
        # 1. Recommendation executable check
        for rec in report.recommendations:
            if rec.executable is True or rec.status != "draft" or rec.risk_class != "proposal":
                return "policy_blocked"
            for pattern in FORBIDDEN_INTENT_PATTERNS:
                if pattern.search(rec.rationale) or pattern.search(rec.action_kind):
                    return "policy_blocked"

        # 2. Findings & hypotheses forbidden intent check
        for f in report.verified_findings:
            for pattern in FORBIDDEN_INTENT_PATTERNS:
                if pattern.search(f.statement):
                    return "policy_blocked"

        for h in report.hypotheses:
            for pattern in FORBIDDEN_INTENT_PATTERNS:
                if pattern.search(h.statement):
                    return "policy_blocked"

        return "pass"

