"""AST analysis and baseline inspection helpers for legacy modules."""
from __future__ import annotations

import ast
from pathlib import Path


def resolve_project_root(base_dir: Path | None = None) -> Path:
    """Dynamically determine the project root directory across CI/local environments."""
    if base_dir is not None:
        return base_dir
    candidate = Path(__file__).resolve().parents[5]
    if (candidate / "src").exists():
        return candidate
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").exists() or (parent / "src" / "risk_dashboard").exists():
            return parent
    return candidate


def extract_ast_definitions(filepath: Path) -> list[str]:
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


def extract_routes(filepath: Path) -> list[str]:
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


def count_tests_in_file(filepath: Path) -> int:
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


def scan_identity_debt(mod_dir: Path, module_slug: str) -> tuple[str, ...]:
    """Dynamically scan module AST for session_id usage and identity debt."""
    debt: list[str] = []
    api_file = mod_dir / "api" / "public.py"
    if api_file.exists():
        try:
            tree = ast.parse(api_file.read_text("utf-8"), filename=str(api_file))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for arg in node.args.args + node.args.kwonlyargs:
                        if arg.arg == "session_id":
                            debt.append(
                                f"{module_slug}/api/public.py:{node.lineno} ({node.name}) "
                                f"accepts client-supplied session_id (violates Module 01 AuthPrincipal P0)"
                            )
        except Exception:
            pass

    schemas_file = mod_dir / "schemas" / "requests.py"
    if schemas_file.exists():
        try:
            tree = ast.parse(schemas_file.read_text("utf-8"), filename=str(schemas_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    if node.target.id == "session_id":
                        debt.append(
                            f"{module_slug}/schemas/requests.py:{node.lineno} has session_id field "
                            f"(violates Module 01 AuthPrincipal P0)"
                        )
        except Exception:
            pass

    if debt:
        debt.append(
            f"Requires migration from session_id to server-resolved account_id via AuthPrincipal"
        )
        debt.append(
            f"Database schema for {module_slug} retains session_id/user_id foreign keys instead of account_id"
        )
    return tuple(debt)
