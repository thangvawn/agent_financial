from __future__ import annotations

import json
from pathlib import Path
import pytest
import yaml

from risk_dashboard.app.bootstrap.app_factory import create_app

SPEC_PATH = Path("docs/api/learning.yaml")
EXAMPLES_DIR = Path("examples")


@pytest.fixture(scope="module")
def openapi_spec() -> dict:
    assert SPEC_PATH.exists(), f"Missing spec {SPEC_PATH}"
    with SPEC_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def app_openapi() -> dict:
    return create_app().openapi()


def test_01_openapi_spec_file_exists(openapi_spec: dict) -> None:
    assert isinstance(openapi_spec, dict)
    assert openapi_spec.get("openapi") == "3.1.0"
    assert "Learning" in openapi_spec.get("info", {}).get("title", "")


def test_02_openapi_spec_paths_present(openapi_spec: dict) -> None:
    paths = openapi_spec.get("paths", {})
    for path, method in [
        ("/api/v1/public/learning/checkpoint", "get"),
        ("/api/v1/public/learning/checkpoint/grade", "post"),
        ("/api/v1/public/learning/checkpoint/complete", "post"),
    ]:
        assert path in paths, f"Path {path} not in spec"
        assert method in paths[path], f"Method {method} not in {path}"


def test_03_openapi_spec_get_checkpoint_schema(openapi_spec: dict) -> None:
    op = openapi_spec["paths"]["/api/v1/public/learning/checkpoint"]["get"]
    param_names = [p.get("name") for p in op.get("parameters", [])]
    assert "lesson_id" in param_names
    assert "200" in op.get("responses", {})


def test_04_openapi_spec_post_grade_schema(openapi_spec: dict) -> None:
    op = openapi_spec["paths"]["/api/v1/public/learning/checkpoint/grade"]["post"]
    assert "application/json" in op.get("requestBody", {}).get("content", {})
    assert "200" in op.get("responses", {})


def test_05_openapi_spec_post_complete_schema(openapi_spec: dict) -> None:
    op = openapi_spec["paths"]["/api/v1/public/learning/checkpoint/complete"]["post"]
    assert "application/json" in op.get("requestBody", {}).get("content", {})
    assert "200" in op.get("responses", {})


def test_06_example_socratic_hint_zero_leakage() -> None:
    data = json.loads((EXAMPLES_DIR / "socratic_hint.json").read_text(encoding="utf-8"))
    assert "lesson_id" in data
    assert any(k in data for k in ("prompt", "hint", "question"))
    assert "correct_answer" not in data and "answer_key" not in data


def test_07_example_checkpoint_grade_structure() -> None:
    data = json.loads((EXAMPLES_DIR / "checkpoint_grade.json").read_text(encoding="utf-8"))
    assert "checkpoint_id" in data
    assert "score" in data or "passed" in data


def test_08_example_checkpoint_complete_idempotency() -> None:
    data = json.loads((EXAMPLES_DIR / "checkpoint_complete.json").read_text(encoding="utf-8"))
    assert "verified_event_id" in data
    assert "idempotency_key" in data


def test_09_fastapi_openapi_learning_tags(app_openapi: dict) -> None:
    paths = app_openapi.get("paths", {})
    for ep, m in [
        ("/api/v1/public/learning/checkpoint", "get"),
        ("/api/v1/public/learning/checkpoint/grade", "post"),
        ("/api/v1/public/learning/checkpoint/complete", "post"),
    ]:
        assert "Learning" in paths[ep][m].get("tags", [])


def test_10_fastapi_openapi_descriptions(app_openapi: dict) -> None:
    paths = app_openapi.get("paths", {})
    for ep, m in [
        ("/api/v1/public/learning/checkpoint", "get"),
        ("/api/v1/public/learning/checkpoint/grade", "post"),
        ("/api/v1/public/learning/checkpoint/complete", "post"),
    ]:
        desc = paths[ep][m].get("description", "")
        assert desc and len(desc.strip()) > 10
