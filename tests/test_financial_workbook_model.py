from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.platform.database.config import clear_db_path_cache


@pytest.fixture
def isolated_workbook_db(tmp_path, monkeypatch):
    monkeypatch.setenv("RISK_DASHBOARD_DB_PATH", str(tmp_path / "northstar.db"))
    clear_db_path_cache()
    yield
    clear_db_path_cache()


def test_workbook_model_is_versioned_and_session_scoped(isolated_workbook_db):
    client = TestClient(app)
    headers_a = {"X-Session-ID": "student-a"}
    headers_b = {"X-Session-ID": "student-b"}
    payload = {
        "expected_revision": 0,
        "active_tab": "ratios",
        "formula": "=NET_INCOME / REVENUE",
        "assumptions": {"revenueGrowthPct": 5},
        "notes": "Đối chiếu với kỳ trước",
    }

    saved = client.post("/financials/FPT/model", json=payload, headers=headers_a)
    assert saved.status_code == 200, saved.text
    assert saved.json()["model"]["revision"] == 1

    loaded = client.get("/financials/FPT/model", headers=headers_a)
    assert loaded.status_code == 200
    assert loaded.json()["model"]["notes"] == payload["notes"]
    assert client.get("/financials/FPT/model", headers=headers_b).status_code == 404

    conflict = client.post("/financials/FPT/model", json=payload, headers=headers_a)
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["current_revision"] == 1

    payload["expected_revision"] = 1
    updated = client.post("/financials/FPT/model", json=payload, headers=headers_a)
    assert updated.status_code == 200
    assert updated.json()["model"]["revision"] == 2
