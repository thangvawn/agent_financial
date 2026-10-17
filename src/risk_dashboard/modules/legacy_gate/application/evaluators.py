"""Gate definitions and baseline report builder for Module 12."""
from __future__ import annotations

import ast
from pathlib import Path

from risk_dashboard.app.config.settings import get_settings
from risk_dashboard.modules.legacy_gate.domain.entities import (
    GateCheckItem,
    LegacyModuleBaselineReport,
    utc_now_iso,
)
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


def _extract_ast_definitions(filepath: Path) -> list[str]:
    """Extract class and function definition names from a python file."""
    if not filepath.exists():
        return []
    try:
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(filepath))
        names: list[str] = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not node.name.startswith("_"):
                    names.append(node.name)
        return names
    except Exception:
        return []


def _extract_routes(filepath: Path) -> list[str]:
    """Extract route definitions from api/public.py."""
    if not filepath.exists():
        return []
    routes: list[str] = []
    try:
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(filepath))
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                        if dec.func.attr in {"get", "post", "put", "delete", "patch"}:
                            path_str = ""
                            if dec.args and isinstance(dec.args[0], ast.Constant):
                                path_str = str(dec.args[0].value)
                            routes.append(f"{dec.func.attr.upper()} {path_str}")
    except Exception:
        pass
    return routes


def _count_tests_in_file(filepath: Path) -> int:
    """Count test methods/functions in a test file."""
    if not filepath.exists():
        return 0
    count = 0
    try:
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(filepath))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("test_"):
                    count += 1
    except Exception:
        pass
    return count


def build_baseline_report(
    module_slug: str,
    base_dir: Path | None = None,
) -> LegacyModuleBaselineReport:
    """Scan legacy module package and return comprehensive baseline report."""
    if module_slug not in {"goals", "financial_health", "community", "guided_investing"}:
        raise LegacyGateError(
            f"Module '{module_slug}' is not a recognized legacy module.",
            error_type="module_not_found",
            module_slug=module_slug,
        )

    # Resolve from the installed application rather than a developer-specific
    # absolute path.  This keeps the gate report usable in Docker, CI and
    # local checkouts with different workspace locations.
    root = base_dir or get_settings().project_root
    mod_dir = root / "src" / "risk_dashboard" / "modules" / module_slug

    if not mod_dir.exists():
        raise LegacyGateError(
            f"Module directory for '{module_slug}' not found at {mod_dir}",
            error_type="module_not_found",
            module_slug=module_slug,
        )

    # 1. Inspect domain entities, policies, services, schemas, routes
    entities = _extract_ast_definitions(mod_dir / "domain" / "entities.py")
    policies = _extract_ast_definitions(mod_dir / "domain" / "policies.py")
    services = _extract_ast_definitions(mod_dir / "application" / "services.py")

    schemas_req = _extract_ast_definitions(mod_dir / "schemas" / "requests.py")
    schemas_resp = _extract_ast_definitions(mod_dir / "schemas" / "responses.py")
    schemas = sorted(set(schemas_req + schemas_resp))

    routes = _extract_routes(mod_dir / "api" / "public.py")

    # 2. Count baseline tests
    test_dir = root / "tests" / "modules" / module_slug
    test_files: list[str] = []
    tests_count = 0
    if test_dir.exists():
        for test_file in sorted(test_dir.glob("test_*.py")):
            rel_path = str(test_file.relative_to(root))
            test_files.append(rel_path)
            tests_count += _count_tests_in_file(test_file)

    # Fallback to check legacy test file if no tests in tests/modules/{slug}
    if tests_count == 0:
        legacy_test = root / "tests" / f"test_{module_slug}.py"
        if legacy_test.exists():
            test_files.append(str(legacy_test.relative_to(root)))
            tests_count += _count_tests_in_file(legacy_test)

    # 3. Read ARCHIVE.md
    archive_file = mod_dir / "ARCHIVE.md"
    archived_reason = "Archived legacy module (unmounted from registry)"
    archived_phase = "Phase 4"
    if archive_file.exists():
        text = archive_file.read_text(encoding="utf-8").strip()
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if lines:
            archived_reason = lines[0].lstrip("#").strip()
        if "Phase 2" in text:
            archived_phase = "Phase 2"
        elif "Phase 4" in text:
            archived_phase = "Phase 4"

    # 4. Identify Identity Debt Notes (session_id usage)
    identity_debt: list[str] = [
        f"{module_slug}/api/public.py accepts client-supplied session_id as user "
        "identifier (violates Module 01 AuthPrincipal P0)",
        "Requires migration from session_id query/body parameters to server-resolved "
        "account_id via AuthPrincipal",
        f"Database schema for {module_slug} retains session_id/user_id foreign keys "
        "instead of account_id",
    ]

    return LegacyModuleBaselineReport(
        module_slug=module_slug,
        schema_version="1.0.0",
        entities_defined=tuple(entities),
        policies_defined=tuple(policies),
        services_defined=tuple(services),
        schemas_defined=tuple(schemas),
        routes_defined=tuple(routes),
        tests_count=tests_count,
        test_files=tuple(test_files),
        archived_reason=archived_reason,
        archived_phase=archived_phase,
        captured_at=utc_now_iso(),
        identity_debt_notes=tuple(identity_debt),
    )
