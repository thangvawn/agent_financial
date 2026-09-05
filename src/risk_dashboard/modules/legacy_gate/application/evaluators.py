"""Gate evaluators and baseline report scanner for Module 12."""
from __future__ import annotations

from pathlib import Path

from risk_dashboard.modules.legacy_gate.application.catalog import get_module_gates
from risk_dashboard.modules.legacy_gate.application.scanner_helpers import (
    count_tests_in_file,
    extract_ast_definitions,
    extract_routes,
    resolve_project_root,
    scan_identity_debt,
)
from risk_dashboard.modules.legacy_gate.domain.entities import (
    GateCheckItem,
    LegacyModuleBaselineReport,
    utc_now_iso,
)
from risk_dashboard.modules.legacy_gate.domain.errors import LegacyGateError


class DefaultGateEvaluator:
    """Default implementation of GateEvaluator port."""

    def get_gates_for_module(self, module_slug: str) -> tuple[GateCheckItem, ...]:
        return get_module_gates(module_slug)


class DefaultBaselineScanner:
    """Default implementation of BaselineScanner port."""

    def scan(self, module_slug: str) -> LegacyModuleBaselineReport:
        return build_baseline_report(module_slug)


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

    root = resolve_project_root(base_dir)
    mod_dir = root / "src" / "risk_dashboard" / "modules" / module_slug

    if not mod_dir.exists():
        raise LegacyGateError(
            f"Module directory for '{module_slug}' not found at {mod_dir}",
            error_type="module_not_found",
            module_slug=module_slug,
        )

    # 1. Inspect domain entities, policies, services, schemas, routes
    entities = extract_ast_definitions(mod_dir / "domain" / "entities.py")
    policies = extract_ast_definitions(mod_dir / "domain" / "policies.py")
    services = extract_ast_definitions(mod_dir / "application" / "services.py")

    schemas_req = extract_ast_definitions(mod_dir / "schemas" / "requests.py")
    schemas_resp = extract_ast_definitions(mod_dir / "schemas" / "responses.py")
    schemas = sorted(set(schemas_req + schemas_resp))

    routes = extract_routes(mod_dir / "api" / "public.py")

    # 2. Count baseline tests
    test_dir = root / "tests" / "modules" / module_slug
    test_files: list[str] = []
    tests_count = 0
    if test_dir.exists():
        for test_file in sorted(test_dir.glob("test_*.py")):
            rel_path = str(test_file.relative_to(root))
            test_files.append(rel_path)
            tests_count += count_tests_in_file(test_file)

    # Fallback to check legacy test file if no tests in tests/modules/{slug}
    if tests_count == 0:
        legacy_test = root / "tests" / f"test_{module_slug}.py"
        if legacy_test.exists():
            test_files.append(str(legacy_test.relative_to(root)))
            tests_count += count_tests_in_file(legacy_test)

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

    # 4. Dynamically scan AST for identity debt
    identity_debt = scan_identity_debt(mod_dir, module_slug)

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
        identity_debt_notes=identity_debt,
    )
