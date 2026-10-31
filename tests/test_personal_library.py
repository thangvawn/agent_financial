"""Personal PDF shelf: real auth, isolated DB/files, no default-data resets."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from risk_dashboard.app.bootstrap.app_factory import create_app  # noqa: F401 - initialize registry
from risk_dashboard.modules.auth.application.services import RegisterAccount
from risk_dashboard.modules.auth.infrastructure.sqlite import (
    SqliteAccountRepository,
    SqliteAccountSessionRepository,
)
from risk_dashboard.modules.learning.api.public import router
from risk_dashboard.platform.database.config import clear_db_path_cache

BASE = "/api/v1/public/learning/library"


def sample_pdf():
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R 4 0 R 5 0 R] /Count 3 >>",
        *[b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 400] >>"] * 3,
    ]
    body, offsets = b"%PDF-1.4\n", [0]
    for number, value in enumerate(objects, 1):
        offsets.append(len(body))
        body += f"{number} 0 obj\n".encode() + value + b"\nendobj\n"
    xref = len(body)
    body += f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode()
    body += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
    return (
        body
        + f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )


@pytest.fixture
def library(tmp_path, monkeypatch):
    for key in ("RISK_DASHBOARD_DB_PATH", "RISK_DASHBOARD_APP_STATE_DB"):
        monkeypatch.setenv(key, str(tmp_path / "shelf.db"))
    clear_db_path_cache()
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/public")
    headers = []
    for suffix in ("a", "b"):
        _, session = RegisterAccount(
            accounts=SqliteAccountRepository(), sessions=SqliteAccountSessionRepository()
        ).execute(
            name=f"Reader {suffix}", email=f"{suffix}@shelf.test", password="shelf-test-password"
        )
        headers.append({"Authorization": f"Bearer {session.session_id}"})
    with TestClient(app) as client:
        yield client, *headers, tmp_path
    clear_db_path_cache()


def upload(client, headers, **metadata):
    return client.post(
        BASE + "/uploads",
        headers=headers,
        data={"title": "PDF của tôi", "kind": "book", **metadata},
        files={"file": ("my-book.pdf", sample_pdf(), "application/pdf")},
    )


def catalog_item(**patch):
    return {
        "title": "Full textbook",
        "author": "Open author",
        "kind": "book",
        "source_url": "/learning-assets/books/full.pdf",
        "page_count": 50,
        **patch,
    }


@pytest.mark.parametrize("method,path", [("get", ""), ("post", "/uploads"), ("post", "/items")])
def test_private_library_requires_real_account(library, method, path):
    client, _, _, _ = library
    assert getattr(client, method)(BASE + path).status_code == 401


@pytest.mark.parametrize("kind", ["book", "paper", "document"])
def test_upload_persists_and_serves_original_pdf(library, kind):
    client, owner, _, _ = library
    response = upload(client, owner, kind=kind, author="Tác giả")
    assert response.status_code == 201, response.text
    item = response.json()
    assert item["kind"] == kind and item["page_count"] == 3
    assert item["status"] == "want_to_read" and item["read_count"] == 0
    assert item["origin"] == "upload" and item["size_bytes"] == len(sample_pdf())
    assert "storage_name" not in item and "account_id" not in item
    saved = client.get(BASE, headers=owner).json()
    assert saved["items"] == [item]
    assert saved["used_bytes"] == len(sample_pdf())
    file = client.get(item["file_url"], headers=owner)
    assert file.content == sample_pdf() and file.headers["content-type"] == "application/pdf"
    assert "no-store" in file.headers["cache-control"]
    part = client.get(item["file_url"], headers={**owner, "Range": "bytes=0-4"})
    assert part.status_code == 206 and part.content == b"%PDF-"


def test_file_metadata_and_history_are_owner_scoped(library):
    client, owner, other, _ = library
    response = upload(client, owner)
    assert response.status_code == 201
    item = response.json()
    path = BASE + "/items/" + item["id"]
    assert client.get(BASE, headers=other).json()["items"] == []
    assert client.get(item["file_url"]).status_code == 401
    assert client.get(item["file_url"], headers=other).status_code == 404
    assert client.get(path, headers=other).status_code == 404
    assert client.patch(path, headers=other, json={"status": "completed"}).status_code == 404
    assert (
        client.post(
            path + "/open", headers=other, json={"event_id": "read-foreign-0001"}
        ).status_code
        == 404
    )
    assert client.delete(path, headers=other).status_code == 404
    assert client.get(item["file_url"], headers=owner).content == sample_pdf()


@pytest.mark.parametrize(
    "filename,content,mime",
    [
        ("bad.pdf", b"<html>not pdf</html>", "application/pdf"),
        ("bad.pdf", b"%PDF-1.4\nfake\n%%EOF", "application/pdf"),
        ("bad.pdf", b"", "application/pdf"),
        ("book.html", sample_pdf(), "application/pdf"),
        ("book.pdf", sample_pdf(), "text/html"),
        ("truncated.pdf", sample_pdf()[:-20], "application/pdf"),
    ],
)
def test_bad_upload_does_not_create_rows_or_files(library, filename, content, mime):
    client, owner, _, root = library
    response = client.post(
        BASE + "/uploads",
        headers=owner,
        data={"title": "Bad", "kind": "book"},
        files={"file": (filename, content, mime)},
    )
    assert response.status_code == 422, response.text
    assert client.get(BASE, headers=owner).json()["items"] == []
    assert not list(root.rglob("*.pdf")) and not list(root.rglob("*.part"))


def test_duplicate_upload_is_idempotent_per_owner(library):
    client, owner, other, root = library
    one, two = upload(client, owner), upload(client, owner, title="Second name")
    assert one.status_code == 201 and two.status_code == 200
    assert one.json()["id"] == two.json()["id"]
    assert two.json()["title"] == "PDF của tôi"
    assert len(client.get(BASE, headers=owner).json()["items"]) == 1
    assert upload(client, other).status_code == 201
    assert len(list(root.rglob("*.pdf"))) == 2


def test_catalog_save_open_history_and_reading_status(library):
    client, owner, _, _ = library
    response = client.post(BASE + "/items", headers=owner, json=catalog_item())
    assert response.status_code == 200, response.text
    item = response.json()
    repeated = client.post(BASE + "/items", headers=owner, json=catalog_item(title="No overwrite"))
    assert repeated.json()["id"] == item["id"]
    assert repeated.json()["title"] == item["title"]
    path = BASE + "/items/" + item["id"]
    assert item["last_opened_at"] is None
    opened = client.post(path + "/open", headers=owner, json={"event_id": "reader-open-0001"})
    assert opened.status_code == 200
    assert opened.json()["read_count"] == 1 and opened.json()["status"] == "reading"
    assert opened.json()["first_opened_at"] == opened.json()["last_opened_at"]
    again = client.post(path + "/open", headers=owner, json={"event_id": "reader-open-0001"})
    assert again.json()["read_count"] == 1
    assert again.json()["last_opened_at"] == opened.json()["last_opened_at"]
    saved = client.patch(path, headers=owner, json={"status": "completed", "current_page": 28})
    assert saved.status_code == 200 and saved.json()["completed_at"]
    assert saved.json()["current_page"] == 28
    reopen = client.post(path + "/open", headers=owner, json={"event_id": "reader-open-0002"})
    assert reopen.json()["status"] == "completed" and reopen.json()["read_count"] == 2
    assert reopen.json()["current_page"] == 28
    restarted = client.patch(path, headers=owner, json={"status": "reading"})
    assert restarted.json()["completed_at"] is None


@pytest.mark.parametrize(
    "source",
    [
        "javascript:alert(1)",
        "//evil.test/a.pdf",
        "/api/v1/public/learning/library/items/other/file.pdf",
        "/etc/passwd",
        "file:///a.pdf",
        "https://user:secret@example.com/a.pdf",
        "/learning-assets/books/../secret.pdf",
    ],
)
def test_catalog_rejects_unsafe_or_private_urls(library, source):
    client, owner, _, _ = library
    assert (
        client.post(
            BASE + "/items", headers=owner, json=catalog_item(source_url=source)
        ).status_code
        == 422
    )


def test_edit_delete_and_invalid_progress(library):
    client, owner, _, root = library
    response = upload(client, owner)
    assert response.status_code == 201
    item = response.json()
    path = BASE + "/items/" + item["id"]
    for patch in (
        {"status": "invalid"},
        {"current_page": 0},
        {"current_page": 4},
        {"title": "   "},
        {"title": None},
        {"storage_name": "../other.pdf"},
    ):
        assert client.patch(path, headers=owner, json=patch).status_code == 422
    updated = client.patch(
        path, headers=owner, json={"title": "Tên mới", "author": "An", "kind": "paper"}
    )
    assert updated.status_code == 200 and updated.json()["kind"] == "paper"
    assert client.delete(path, headers=owner).status_code == 204
    assert client.get(item["file_url"], headers=owner).status_code == 404
    assert client.get(BASE, headers=owner).json()["items"] == []
    assert not list(root.rglob("*.pdf"))


def test_upload_filename_cannot_control_storage_path(library):
    client, owner, _, root = library
    result = client.post(
        BASE + "/uploads",
        headers=owner,
        data={"title": "Safe", "kind": "document"},
        files={"file": ("../../outside.pdf", sample_pdf(), "application/pdf")},
    )
    assert result.status_code == 201
    files = list(root.rglob("*.pdf"))
    assert len(files) == 1 and files[0].parent == root / "learning_library_files"
    assert files[0].name != "outside.pdf"


def test_revoked_session_cannot_access_uploaded_file(library):
    client, owner, _, _ = library
    result = upload(client, owner)
    assert result.status_code == 201
    SqliteAccountSessionRepository().revoke(session_id=owner["Authorization"].split()[1])
    assert client.get(result.json()["file_url"], headers=owner).status_code == 401
    assert client.get(BASE, headers=owner).status_code == 401


def test_upload_limits_and_quota_leave_no_partial_files(library, monkeypatch):
    from risk_dashboard.modules.learning.infrastructure import personal_library as storage

    client, owner, _, root = library
    monkeypatch.setattr(storage, "MAX_UPLOAD_BYTES", 100)
    assert upload(client, owner).status_code == 413
    assert not list(root.rglob("*.part")) and not list(root.rglob("*.pdf"))
    monkeypatch.setattr(storage, "MAX_UPLOAD_BYTES", 40 * 1024 * 1024)
    monkeypatch.setattr(storage, "MAX_ACCOUNT_BYTES", 100)
    assert upload(client, owner).status_code == 413
    assert client.get(BASE, headers=owner).json()["items"] == []
    assert not list(root.rglob("*.pdf"))
    monkeypatch.setattr(storage, "MAX_ACCOUNT_ITEMS", 0)
    assert client.post(BASE + "/items", headers=owner, json=catalog_item()).status_code == 413


def test_declared_and_streamed_request_limits(library, monkeypatch):
    from risk_dashboard.modules.learning.infrastructure import personal_library as storage

    client, owner, _, _ = library
    monkeypatch.setattr(storage, "MAX_UPLOAD_BYTES", 100)
    headers = {**owner, "content-type": "multipart/form-data; boundary=shelf-boundary"}
    declared = client.post(
        BASE + "/uploads", headers={**headers, "content-length": "999999"}, content=b"x"
    )
    assert declared.status_code == 413

    def body():
        yield b'--shelf-boundary\r\nContent-Disposition: form-data; name="file"; filename="book.pdf"\r\nContent-Type: application/pdf\r\n\r\n'
        yield b"x" * 70000
        yield b"\r\n--shelf-boundary--\r\n"

    streamed = client.post(BASE + "/uploads", headers=headers, content=body())
    assert streamed.status_code == 413, streamed.text


@pytest.mark.parametrize("metadata", [{"title": " "}, {"kind": "video"}, {"title": "a" * 241}])
def test_upload_metadata_validation(library, metadata):
    client, owner, _, _ = library
    assert upload(client, owner, **metadata).status_code == 422


def test_duplicate_after_reading_preserves_state_and_quota(library):
    client, owner, _, _ = library
    item = upload(client, owner).json()
    path = BASE + "/items/" + item["id"]
    client.patch(path, headers=owner, json={"status": "completed", "current_page": 3})
    same = upload(client, owner).json()
    assert same["status"] == "completed" and same["current_page"] == 3
    assert client.get(BASE, headers=owner).json()["used_bytes"] == len(sample_pdf())


def test_missing_file_catalog_file_and_removed_history(library):
    client, owner, _, root = library
    ref = client.post(
        BASE + "/items", headers=owner, json=catalog_item(source_id="original-id")
    ).json()
    assert ref["source_id"] == "original-id"
    assert client.get(BASE + "/items/" + ref["id"] + "/file.pdf", headers=owner).status_code == 404
    item = upload(client, owner).json()
    next(root.rglob("*.pdf")).unlink()
    assert client.get(item["file_url"], headers=owner).status_code == 404
    assert client.delete(BASE + "/items/" + item["id"], headers=owner).status_code == 204
    assert client.get(BASE + "/items/missing", headers=owner).status_code == 404
