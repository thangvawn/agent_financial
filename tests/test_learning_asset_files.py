"""Bundled books must be served even when the writable data volume is empty."""
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from risk_dashboard.app.bootstrap import app_factory


@pytest.fixture
def assets(tmp_path, monkeypatch):
    settings = replace(
        app_factory.get_settings(),
        project_root=tmp_path,
        frontend_dist=tmp_path / "frontend" / "dist",
        learning_assets_dir=tmp_path / "data" / "learning_assets",
    )
    for directory in (
        settings.learning_assets_dir,
        settings.frontend_dist / "learning-assets" / "books",
        tmp_path / "frontend" / "public" / "learning-assets" / "books",
    ):
        directory.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(app_factory, "get_settings", lambda: settings)
    return settings, tmp_path


def test_bundled_pdf_is_served_with_range_support(assets):
    settings, _ = assets
    body = b"%PDF-1.4\nfull book\n%%EOF"
    (settings.frontend_dist / "learning-assets/books/book.pdf").write_bytes(body)
    client = TestClient(app_factory.create_app())
    response = client.get("/learning-assets/books/book.pdf", headers={"Range": "bytes=0-4"})
    assert response.status_code == 206
    assert response.content == b"%PDF-"
    assert client.get("/learning-assets/books/book.pdf").content == body


def test_user_asset_takes_precedence_over_bundle(assets):
    settings, _ = assets
    (settings.learning_assets_dir / "books").mkdir()
    (settings.learning_assets_dir / "books/book.pdf").write_bytes(b"user-owned file")
    (settings.frontend_dist / "learning-assets/books/book.pdf").write_bytes(b"bundled file")
    assert TestClient(app_factory.create_app()).get("/learning-assets/books/book.pdf").content == b"user-owned file"


def test_public_assets_work_before_frontend_build(assets):
    _, root = assets
    (root / "frontend/public/learning-assets/books/new.pdf").write_bytes(b"%PDF-1.4\n%%EOF")
    assert TestClient(app_factory.create_app()).get("/learning-assets/books/new.pdf").status_code == 200


def test_missing_and_escaped_paths_remain_404(assets):
    settings, root = assets
    (root / "private.txt").write_text("private fixture")
    (settings.frontend_dist / "learning-assets/books/escaped.pdf").symlink_to(root / "private.txt")
    client = TestClient(app_factory.create_app())
    for path in ("/learning-assets/books/missing.pdf", "/learning-assets/%2e%2e/private.txt", "/learning-assets/books/escaped.pdf"):
        assert client.get(path).status_code == 404
