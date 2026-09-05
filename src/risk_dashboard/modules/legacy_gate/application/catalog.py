"""Gate definitions and catalog for Module 12."""
from __future__ import annotations

from risk_dashboard.modules.legacy_gate.domain.entities import GateCheckItem
from risk_dashboard.modules.legacy_gate.domain.errors import LegacyGateError


def _make_common_gates(slug: str) -> tuple[GateCheckItem, ...]:
    return (
        GateCheckItem(
            gate_id=f"{slug}-1",
            category="product",
            description="Product owner and target user/outcome defined",
        ),
        GateCheckItem(
            gate_id=f"{slug}-2",
            category="data",
            description="Source of truth, API, data ownership, maintainer confirmed",
        ),
        GateCheckItem(
            gate_id=f"{slug}-3",
            category="maintenance",
            description="Archived reason resolved via ADR",
        ),
        GateCheckItem(
            gate_id=f"{slug}-4",
            category="security",
            description="Auth/account migration and retention complete",
        ),
        GateCheckItem(
            gate_id=f"{slug}-5",
            category="regulatory",
            description="Regulatory/advisory boundary reviewed",
        ),
        GateCheckItem(
            gate_id=f"{slug}-6",
            category="maintenance",
            description="Deterministic service/tool baseline passes tests",
        ),
        GateCheckItem(
            gate_id=f"{slug}-7",
            category="security",
            description="Gold set, threat model, feature flag, rollout/rollback exist",
        ),
        GateCheckItem(
            gate_id=f"{slug}-8",
            category="product",
            description="No P0/P1 roadmap degradation",
        ),
    )


GOALS_SPECIFIC = (
    GateCheckItem(
        gate_id="goals-9",
        category="product",
        description="Goal taxonomy and explicit user consent defined",
    ),
    GateCheckItem(
        gate_id="goals-10",
        category="product",
        description="Goal correction/delete/export supported",
    ),
    GateCheckItem(
        gate_id="goals-11",
        category="security",
        description="No inference of sensitive wealth/income from conversation",
    ),
    GateCheckItem(
        gate_id="goals-12",
        category="product",
        description="Deterministic eligibility and next-step plan",
    ),
    GateCheckItem(
        gate_id="goals-13",
        category="regulatory",
        description="Education goal separated from regulated advice",
    ),
    GateCheckItem(
        gate_id="goals-14",
        category="product",
        description="Home integration only via compact summary",
    ),
)

FH_SPECIFIC = (
    GateCheckItem(
        gate_id="fh-9",
        category="security",
        description="Field-level redaction before AI context",
    ),
    GateCheckItem(
        gate_id="fh-10",
        category="regulatory",
        description="High-stakes disclaimer and escalation policy",
    ),
    GateCheckItem(
        gate_id="fh-11",
        category="security",
        description="No inferred wealth profile written to durable memory",
    ),
    GateCheckItem(
        gate_id="fh-12",
        category="product",
        description="Read-only explanation focus (no mutation without consent)",
    ),
)

COM_SPECIFIC = (
    GateCheckItem(
        gate_id="com-9",
        category="security",
        description="Community content treated as untrusted data source",
    ),
    GateCheckItem(
        gate_id="com-10",
        category="security",
        description="Stored prompt injection defense (content isolation)",
    ),
    GateCheckItem(
        gate_id="com-11",
        category="product",
        description="No autonomous posting / no user impersonation",
    ),
    GateCheckItem(
        gate_id="com-12",
        category="product",
        description="Moderated read-only summary only",
    ),
)

GI_SPECIFIC = (
    GateCheckItem(
        gate_id="gi-9",
        category="regulatory",
        description="Legal review: Securities Law 2019 advisory boundary",
    ),
    GateCheckItem(
        gate_id="gi-10",
        category="product",
        description="Education-only scope on paper portfolio",
    ),
    GateCheckItem(
        gate_id="gi-11",
        category="security",
        description="No broker connection / no real order placement",
    ),
    GateCheckItem(
        gate_id="gi-12",
        category="product",
        description="Explicitly approved pilot required",
    ),
)


def get_module_gates(module_slug: str) -> tuple[GateCheckItem, ...]:
    """Return immutable tuple of gates defined for the given legacy module."""
    if module_slug == "goals":
        return _make_common_gates("goals") + GOALS_SPECIFIC
    elif module_slug == "financial_health":
        return _make_common_gates("fh") + FH_SPECIFIC
    elif module_slug == "community":
        return _make_common_gates("com") + COM_SPECIFIC
    elif module_slug == "guided_investing":
        return _make_common_gates("gi") + GI_SPECIFIC
    else:
        raise LegacyGateError(
            f"Unknown legacy module: '{module_slug}'",
            error_type="module_not_found",
            module_slug=module_slug,
        )
