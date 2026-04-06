"""Tests for API middleware (auth, logging)."""
from __future__ import annotations

import os
from unittest import mock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    from risk_dashboard.api.main import app
    return TestClient(app)


def test_health_always_public(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in ("ok", "degraded")
    assert "checks" in body


def test_health_reports_panel_status(client):
    body = client.get("/health").json()
    assert "panel_loaded" in body["checks"]
    assert "model_available" in body["checks"]


def test_api_key_blocks_when_set(client):
    with mock.patch.dict(os.environ, {"API_SECRET_KEY": "test-secret-123"}):
        resp = client.get("/dashboard/state")
        assert resp.status_code == 401

        resp = client.get("/dashboard/state", headers={"X-API-Key": "wrong"})
        assert resp.status_code == 401

        resp = client.get("/dashboard/state", headers={"X-API-Key": "test-secret-123"})
        assert resp.status_code in (200, 503)


def test_api_key_passthrough_when_unset(client):
    with mock.patch.dict(os.environ, {"API_SECRET_KEY": ""}, clear=False):
        resp = client.get("/dashboard/state")
        assert resp.status_code in (200, 503)


def test_docs_endpoint_accessible(client):
    resp = client.get("/docs")
    assert resp.status_code == 200


def test_openapi_has_tags(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    tag_names = [t["name"] for t in schema.get("tags", [])]
    assert "System" in tag_names
    assert "Dashboard" in tag_names
    assert "Quant" in tag_names
    assert "Chat" in tag_names
    assert "Financials" in tag_names
