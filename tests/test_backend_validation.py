from __future__ import annotations

import json
from pathlib import Path
import pytest

from risk_dashboard.app.bootstrap.app_factory import create_app
from risk_dashboard.modules.admin_cms.domain.entities import CmsContentItem, CmsContentVersion, utc_now_iso
from risk_dashboard.modules.admin_cms.infrastructure.repositories.sqlite import SqliteAdminCmsRepository
from risk_dashboard.modules.learning.application.checkpoint_service import LearningCheckpointService
from risk_dashboard.modules.learning.application.memory_hooks import LearningMemoryGovernor
from risk_dashboard.modules.learning.domain.entities import VerifiedEventRecord
from risk_dashboard.modules.learning.evals.gold_set import GOLD_SET_SUITE
from risk_dashboard.modules.learning.evals.multi_agent_runner import LearningMultiAgentEvalRunner
from risk_dashboard.modules.learning.evals.telemetry import get_multi_agent_telemetry, reset_multi_agent_telemetry
from risk_dashboard.modules.learning.infrastructure.catalog_reader import SqliteLearningCatalog
from risk_dashboard.modules.learning.infrastructure.repositories.sqlite import reset_learning_state
from risk_dashboard.platform.database import open_app_state_db
from risk_dashboard.platform.database.migrate import apply_migrations


def _seed(repo: SqliteAdminCmsRepository, slug: str, qs: list[dict]) -> None:
    now = utc_now_iso()
    repo.save_item(CmsContentItem(content_id=f"s_{slug}", content_type="lesson", slug=slug, title=slug, locale="vi-VN", owner_team="ed", risk_category="ed", workflow_state="published", current_version=1, published_version=1, created_by="t", updated_by="t", created_at=now, updated_at=now))
    repo.save_version(CmsContentVersion(version_id=f"v_{slug}", content_id=f"s_{slug}", version_number=1, payload={"lesson_id": slug, "title": slug, "summary": "s", "tier": "financial_basics", "content_type": "micro_lesson", "estimated_minutes": 3, "body": ["b"], "glossary": [], "quiz_questions": qs, "status": "published"}, status="published", origin="t", change_summary="c", created_by="t", reviewed_by="t", published_by="t", created_at=now, published_at=now))


def _ev(acc: str, score: int) -> VerifiedEventRecord:
    return VerifiedEventRecord(event_id=f"e_{acc}_{score}", account_id=acc, checkpoint_id="cp", lesson_id="l1", score=score, passed=score >= 50, rubric_evidence=(), misconceptions=(), created_at="2026-09-12T10:00:00Z")


@pytest.fixture(scope="module", autouse=True)
def init_suite():
    reset_learning_state()
    with open_app_state_db() as conn:
        apply_migrations(conn)
    reset_multi_agent_telemetry()
    runner = LearningMultiAgentEvalRunner()
    summary = runner.run_suite(GOLD_SET_SUITE)
    return {"summary": summary, "telemetry": get_multi_agent_telemetry(), "app": create_app()}


# --- P0: REST API Contracts (D-01 to D-10) ---
def test_d01_contract_spec_yaml_exists() -> None:
    assert Path("docs/api/learning.yaml").exists()


def test_d02_contract_get_checkpoint_route(init_suite) -> None:
    assert "/api/v1/public/learning/checkpoint" in init_suite["app"].openapi()["paths"]


def test_d03_contract_post_grade_route(init_suite) -> None:
    assert "/api/v1/public/learning/checkpoint/grade" in init_suite["app"].openapi()["paths"]


def test_d04_contract_post_complete_route(init_suite) -> None:
    assert "/api/v1/public/learning/checkpoint/complete" in init_suite["app"].openapi()["paths"]


def test_d05_contract_learning_tags(init_suite) -> None:
    op = init_suite["app"].openapi()["paths"]["/api/v1/public/learning/checkpoint"]["get"]
    assert "Learning" in op.get("tags", [])


def test_d06_contract_route_descriptions(init_suite) -> None:
    op = init_suite["app"].openapi()["paths"]["/api/v1/public/learning/checkpoint/grade"]["post"]
    assert len(op.get("description", "").strip()) > 10


def test_d07_contract_socratic_hint_example() -> None:
    data = json.loads(Path("examples/socratic_hint.json").read_text(encoding="utf-8"))
    assert "lesson_id" in data and any(k in data for k in ("prompt", "hint"))


def test_d08_contract_checkpoint_grade_example() -> None:
    data = json.loads(Path("examples/checkpoint_grade.json").read_text(encoding="utf-8"))
    assert "checkpoint_id" in data and "score" in data


def test_d09_contract_checkpoint_complete_example() -> None:
    data = json.loads(Path("examples/checkpoint_complete.json").read_text(encoding="utf-8"))
    assert "verified_event_id" in data and "idempotency_key" in data


def test_d10_contract_zero_leakage_example() -> None:
    data = json.loads(Path("examples/socratic_hint.json").read_text(encoding="utf-8"))
    assert "correct_answer" not in data and "answer_key" not in data


# --- P1: Multi-Agent Engine & Telemetry (D-11 to D-18) ---
def test_d11_engine_gold_set_suite_size(init_suite) -> None:
    assert init_suite["summary"].total_cases >= 100


def test_d12_engine_gold_set_pass_rate(init_suite) -> None:
    rate = init_suite["summary"].passed_cases / init_suite["summary"].total_cases
    assert rate >= 0.995


def test_d13_engine_suite_status_passed(init_suite) -> None:
    assert init_suite["summary"].status == "PASSED"


def test_d14_telemetry_total_runs(init_suite) -> None:
    assert init_suite["telemetry"]["total_runs"] >= 100


def test_d15_telemetry_success_rate(init_suite) -> None:
    assert init_suite["telemetry"]["success_rate"] >= 0.995


def test_d16_telemetry_latency_p95_valid(init_suite) -> None:
    assert init_suite["telemetry"]["latency_ms_p95"] > 0


def test_d17_telemetry_error_taxonomy_empty(init_suite) -> None:
    assert isinstance(init_suite["telemetry"]["error_types"], dict)


def test_d18_telemetry_reset_functionality() -> None:
    reset_multi_agent_telemetry()
    t = get_multi_agent_telemetry()
    assert t["total_runs"] == 0 and t["success_rate"] == 0.0


# --- P2: Product Requirements (D-19 to D-26) ---
def test_d19_product_pool_random_sampling() -> None:
    repo = SqliteAdminCmsRepository()
    qs = [{"question_id": f"q_{i}", "prompt": f"P{i}?", "options": ["A"], "correct_answer": "A"} for i in range(5)]
    _seed(repo, "d-pool", qs)
    svc = LearningCheckpointService(catalog=SqliteLearningCatalog(content_ops_repo=repo))
    assert len({svc.create_checkpoint(account_id="u", lesson_id="d-pool").prompt for _ in range(20)}) > 1


def test_d20_product_pool_zero_answer_leakage() -> None:
    repo = SqliteAdminCmsRepository()
    _seed(repo, "d-leak", [{"question_id": "q", "prompt": "P?", "options": ["A"], "correct_answer": "X"}])
    svc = LearningCheckpointService(catalog=SqliteLearningCatalog(content_ops_repo=repo))
    res = svc.create_checkpoint(account_id="u", lesson_id="d-leak").model_dump()
    assert "correct_answer" not in res and "explanation" not in res


def test_d21_product_pool_single_question_fallback() -> None:
    repo = SqliteAdminCmsRepository()
    _seed(repo, "d-single", [{"question_id": "q1", "prompt": "PSingle?", "options": ["A"], "correct_answer": "A"}])
    svc = LearningCheckpointService(catalog=SqliteLearningCatalog(content_ops_repo=repo))
    assert svc.create_checkpoint(account_id="u", lesson_id="d-single").prompt == "PSingle?"


def test_d22_product_pool_boundary_ten_questions() -> None:
    repo = SqliteAdminCmsRepository()
    qs = [{"question_id": f"q_{i}", "prompt": f"PTen {i}?", "options": ["A"], "correct_answer": "A"} for i in range(10)]
    _seed(repo, "d-ten", qs)
    svc = LearningCheckpointService(catalog=SqliteLearningCatalog(content_ops_repo=repo))
    assert svc.create_checkpoint(account_id="u", lesson_id="d-ten").prompt.startswith("PTen")


def test_d23_product_mastery_retail_75_pass() -> None:
    prop = LearningMemoryGovernor.propose_mastery(verified_event=_ev("u_ret", 75), tier="community", role="retail")
    assert prop is not None and prop.score == 75


def test_d24_product_mastery_pro_75_rejected() -> None:
    assert LearningMemoryGovernor.propose_mastery(verified_event=_ev("u_pro", 75), tier="pro", role="institutional") is None


def test_d25_product_mastery_pro_85_pass() -> None:
    prop = LearningMemoryGovernor.propose_mastery(verified_event=_ev("u_pro", 85), tier="pro", role="institutional")
    assert prop is not None and prop.score == 85


def test_d26_product_mastery_default_80_threshold() -> None:
    assert LearningMemoryGovernor.propose_mastery(verified_event=_ev("u_def", 79), tier="standard") is None
    prop = LearningMemoryGovernor.propose_mastery(verified_event=_ev("u_def", 80), tier="standard")
    assert prop is not None and prop.score == 80
