from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.home_onboarding.infrastructure.repositories.sqlite import reset_home_onboarding_state
from risk_dashboard.modules.pro_lab.infrastructure.repositories.sqlite import reset_pro_lab_state


def test_pro_lab_surface_boundaries(monkeypatch):
    reset_home_onboarding_state()
    reset_pro_lab_state()
    monkeypatch.setenv("PRO_LAB_KEY", "pro-lab-test")
    monkeypatch.setenv("ADMIN_TRADING_LAB_KEY", "admin-lab-test")
    client = TestClient(app)

    session_id = client.post("/api/v1/public/onboarding/start").json()["session_id"]
    complete = client.post(
        "/api/v1/public/onboarding/complete",
        json={
            "session_id": session_id,
            "answers": [
                {"question_key": "primary_goal", "answer_value": "deep_analysis_tools"},
                {"question_key": "knowledge_level", "answer_value": "advanced"},
                {"question_key": "primary_interest", "answer_value": "markets"},
                {"question_key": "current_state", "answer_value": "already_investing_wants_structure"},
                {"question_key": "risk_tolerance_prelim", "answer_value": "moderate"},
            ],
        },
    )
    assert complete.status_code == 200
    assert complete.json()["pro_eligible"] is True

    teaser = client.get(f"/api/v1/public/pro-lab/teaser?session_id={session_id}")
    assert teaser.status_code == 200
    assert teaser.json()["pro_eligible"] is True
    assert teaser.json()["enabled"] is True

    access = client.post(
        "/api/v1/public/pro-lab/access-token",
        json={"session_id": session_id},
    )
    assert access.status_code == 200
    access_token = access.json()["access_token"]

    sessions = client.get(
        f"/api/v1/pro/pro-lab/sessions?user_id={session_id}",
        headers={"X-Access-Token": access_token},
    )
    assert sessions.status_code == 200
    assert sessions.json()["sessions"]
    assert sessions.json()["sessions"][0]["token_id"] == access_token
    assert sessions.json()["sessions"][0]["status"] == "active"

    blueprint = client.post(
        "/api/v1/pro/pro-lab/blueprints",
        headers={"X-Access-Token": access_token},
        json={
            "user_id": session_id,
            "name": "VN Quality Rotation",
            "objective": "Tao workspace premium de benchmark va stress-test strategy blueprint co caveat ro rang.",
            "asset_universe": ["FPT", "VCB", "MWG"],
            "benchmark": "VNINDEX",
            "rebalance_frequency": "monthly",
            "risk_constraints": "Max concentration 35%, no single-theme overload",
            "assumptions_note": "Khong dung de phat tin hieu cong khai.",
        },
    )
    assert blueprint.status_code == 200
    blueprint_id = blueprint.json()["blueprint_id"]

    workspace = client.get(
        f"/api/v1/pro/pro-lab/workspace?user_id={session_id}",
        headers={"X-Access-Token": access_token},
    )
    assert workspace.status_code == 200
    assert workspace.json()["blueprints"]
    assert any(item["id"] == "strategy_copilot" for item in workspace.json()["capability_cards"])

    catalog = client.get(
        "/api/v1/pro/pro-lab/catalog",
        headers={"X-Access-Token": access_token},
    )
    assert catalog.status_code == 200
    provider_ids = {item["provider_id"] for item in catalog.json()["providers"]}
    assert {
        "strategy_copilot",
        "swarm_committee",
        "validation_lab",
        "optimizer_lab",
        "data_router",
        "export_lab",
        "journal_lab",
    }.issubset(provider_ids)

    updated = client.patch(
        f"/api/v1/pro/pro-lab/blueprints/{blueprint_id}",
        headers={"X-Access-Token": access_token},
        json={
            "user_id": session_id,
            "name": "VN Quality Rotation v2",
            "benchmark": "VN30",
            "risk_constraints": "Max concentration 25%, lower single-theme risk",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "VN Quality Rotation v2"

    second_blueprint = client.post(
        "/api/v1/pro/pro-lab/blueprints",
        headers={"X-Access-Token": access_token},
        json={
            "user_id": session_id,
            "name": "VN Defensive Basket",
            "objective": "Tao blueprint thu hai de compare benchmark va cadence.",
            "asset_universe": ["VCB", "VNM"],
            "benchmark": "VNINDEX",
            "rebalance_frequency": "quarterly",
            "risk_constraints": "Defensive bias, lower turnover",
            "assumptions_note": "Khong dung nhu signal retail.",
        },
    )
    assert second_blueprint.status_code == 200
    second_blueprint_id = second_blueprint.json()["blueprint_id"]

    compare = client.get(
        "/api/v1/pro/pro-lab/blueprints/compare",
        params={"user_id": session_id, "left_id": blueprint_id, "right_id": second_blueprint_id},
        headers={"X-Access-Token": access_token},
    )
    assert compare.status_code == 200
    assert compare.json()["differences"]

    scenario = client.post(
        "/api/v1/pro/pro-lab/scenario-lab/run",
        headers={"X-Access-Token": access_token},
        json={
            "user_id": session_id,
            "blueprint_id": blueprint_id,
            "scenario_preset": "fx_stress",
            "usd_vnd_rate": 25850,
            "sbv_interest_rate_pct": 4.5,
        },
    )
    assert scenario.status_code == 200
    assert scenario.json()["experiment_type"] == "scenario_lab"

    strategy_draft = client.post(
        "/api/v1/pro/pro-lab/runs",
        headers={"X-Access-Token": access_token},
        json={
            "user_id": session_id,
            "blueprint_id": blueprint_id,
            "provider_id": "strategy_copilot",
            "command_id": "natural_language_strategy",
            "input_payload": {
                "idea": "Quality rotation with momentum confirmation",
                "market": "Vietnam equities",
                "horizon": "monthly",
                "risk_budget_pct": 2,
            },
        },
    )
    assert strategy_draft.status_code == 200
    assert strategy_draft.json()["provider_id"] == "strategy_copilot"
    assert "strategy_draft" in strategy_draft.json()["output_payload"]

    swarm_review = client.post(
        "/api/v1/pro/pro-lab/runs",
        headers={"X-Access-Token": access_token},
        json={
            "user_id": session_id,
            "blueprint_id": blueprint_id,
            "provider_id": "swarm_committee",
            "command_id": "quant_strategy_review",
            "input_payload": {
                "review_focus": "overfit, liquidity and execution assumptions",
                "validation_depth": "standard",
            },
        },
    )
    assert swarm_review.status_code == 200
    assert swarm_review.json()["status"] == "needs_review"
    assert swarm_review.json()["output_payload"]["role_memos"]

    optimizer = client.post(
        "/api/v1/pro/pro-lab/runs",
        headers={"X-Access-Token": access_token},
        json={
            "user_id": session_id,
            "blueprint_id": blueprint_id,
            "provider_id": "optimizer_lab",
            "command_id": "risk_budget_optimizer",
            "input_payload": {"method": "risk_parity", "max_weight_pct": 35, "target_volatility_pct": 18},
        },
    )
    assert optimizer.status_code == 200
    assert optimizer.json()["output_payload"]["allocation"]

    validation = client.post(
        "/api/v1/pro/pro-lab/runs",
        headers={"X-Access-Token": access_token},
        json={
            "user_id": session_id,
            "blueprint_id": blueprint_id,
            "provider_id": "validation_lab",
            "command_id": "walk_forward_monte_carlo",
            "input_payload": {"window_months": 6, "cost_bps": 20, "simulations": 1000},
        },
    )
    assert validation.status_code == 200
    assert validation.json()["output_payload"]["validation_suite"]

    export = client.post(
        "/api/v1/pro/pro-lab/runs",
        headers={"X-Access-Token": access_token},
        json={
            "user_id": session_id,
            "blueprint_id": blueprint_id,
            "provider_id": "export_lab",
            "command_id": "strategy_code_export",
            "input_payload": {"target": "python", "include_alerts": True},
        },
    )
    assert export.status_code == 200
    assert export.json()["output_payload"]["files"]

    journal = client.post(
        "/api/v1/pro/pro-lab/runs",
        headers={"X-Access-Token": access_token},
        json={
            "user_id": session_id,
            "blueprint_id": blueprint_id,
            "provider_id": "journal_lab",
            "command_id": "shadow_account_review",
            "input_payload": {"journal_text": "Followed setup, no FOMO, no oversize.", "max_daily_loss_pct": 1, "max_rule_breaks": 2},
        },
    )
    assert journal.status_code == 200
    assert journal.json()["output_payload"]["discipline_score"] >= 0

    backtest = client.post(
        "/api/v1/pro/pro-lab/backtest-lab/run",
        headers={"X-Access-Token": access_token},
        json={
            "user_id": session_id,
            "blueprint_id": blueprint_id,
            "start_date": "2025-01-01",
            "end_date": "2025-06-30",
            "initial_capital": 100000000,
            "timeframe": "1h",
        },
    )
    assert backtest.status_code == 200
    assert backtest.json()["experiment_type"] == "backtest_lab"
    assert backtest.json()["engine_result"]["interval"] == "1h"

    report = client.get(
        f"/api/v1/pro/pro-lab/experiments/{backtest.json()['experiment_id']}/report",
        params={"user_id": session_id},
        headers={"X-Access-Token": access_token},
    )
    assert report.status_code == 200
    assert report.json()["filename"].endswith(".md")
    assert "Caveats" in report.json()["content"]
    assert report.json()["confidence_label"]
    assert report.json()["what_this_is"]
    assert report.json()["what_this_is_not"]
    assert report.json()["disclaimer_text"]

    archived = client.post(
        f"/api/v1/pro/pro-lab/blueprints/{second_blueprint_id}/archive",
        params={"user_id": session_id},
        headers={"X-Access-Token": access_token},
    )
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"

    admin_access = client.post(
        "/admin/pro-lab/access/bootstrap",
        headers={"X-Admin-Trading-Lab-Key": "admin-lab-test"},
    )
    assert admin_access.status_code == 200
    admin_token = admin_access.json()["access_token"]

    admin_experiments = client.get(
        "/admin/pro-lab/experiments",
        headers={"X-Access-Token": admin_token},
    )
    assert admin_experiments.status_code == 200
    assert admin_experiments.json()["count"] >= 2

    reviewed = client.post(
        f"/admin/pro-lab/experiments/{backtest.json()['experiment_id']}/review",
        headers={"X-Access-Token": admin_token},
        json={"review_status": "approved", "review_notes": "Notebook summary and caveats look acceptable."},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["review_status"] == "approved"
    assert reviewed.json()["reviewer_id"] == "internal-admin"

    admin_audit = client.get(
        "/admin/pro-lab/audit",
        headers={"X-Access-Token": admin_token},
    )
    assert admin_audit.status_code == 200
    assert admin_audit.json()["items"]

    revoked = client.post(
        f"/api/v1/pro/pro-lab/sessions/{access_token}/revoke",
        params={"user_id": session_id},
        headers={"X-Access-Token": access_token},
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"

    sessions_after_revoke = client.get(
        f"/api/v1/pro/pro-lab/sessions?user_id={session_id}",
        headers={"X-Access-Token": admin_token},
    )
    assert sessions_after_revoke.status_code == 200
    revoked_session = next(item for item in sessions_after_revoke.json()["sessions"] if item["token_id"] == access_token)
    assert revoked_session["status"] == "revoked"


def test_pro_lab_local_mode_allows_tokenless_testing(monkeypatch):
    reset_pro_lab_state()
    monkeypatch.setenv("MODE", "development")
    monkeypatch.setenv("PRO_LAB_LOCAL_TEST_OPEN", "1")
    client = TestClient(app)

    workspace = client.get("/api/v1/pro/pro-lab/workspace?user_id=local-tester")
    assert workspace.status_code == 200

    catalog = client.get("/api/v1/pro/pro-lab/catalog")
    assert catalog.status_code == 200
    provider_ids = {item["provider_id"] for item in catalog.json()["providers"]}
    assert "private_auto_copy_trading" in provider_ids
