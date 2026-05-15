from __future__ import annotations

import argparse
import io
import json
import mimetypes
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


DRIVE_FOLDER_MIME = "application/vnd.google-apps.folder"
GOOGLE_EXPORTS = {
    "application/vnd.google-apps.document": ("application/pdf", ".pdf"),
    "application/vnd.google-apps.spreadsheet": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xlsx",
    ),
    "application/vnd.google-apps.presentation": (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".pptx",
    ),
}


@dataclass(frozen=True)
class DriveDownloadedFile:
    file_id: str
    name: str
    mime_type: str
    drive_path: str
    local_path: str
    size_bytes: int
    modified_time: str | None
    web_view_link: str | None


@dataclass(frozen=True)
class DriveFolderSyncManifest:
    sync_id: str
    created_at: str
    folder_name: str
    folder_id: str
    output_dir: str
    downloaded_count: int
    files: list[DriveDownloadedFile]


def sync_drive_folder(
    *,
    credentials_file: str | Path,
    folder_name: str,
    output_dir: str | Path,
    folder_id: str | None = None,
    include_extensions: Iterable[str] | None = None,
    recursive: bool = True,
) -> tuple[Path, DriveFolderSyncManifest]:
    service = build_drive_service(credentials_file)
    resolved_folder_id = folder_id or find_folder_id(service=service, folder_name=folder_name)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    allowed_extensions = normalize_extensions(include_extensions)

    downloaded: list[DriveDownloadedFile] = []
    for item in iter_folder_files(
        service=service,
        folder_id=resolved_folder_id,
        parent_path=folder_name,
        recursive=recursive,
    ):
        if item["mimeType"] == DRIVE_FOLDER_MIME:
            continue
        export_mime, export_extension = GOOGLE_EXPORTS.get(item["mimeType"], (None, None))
        target_name = safe_filename(item["name"])
        if export_extension and not target_name.lower().endswith(export_extension):
            target_name = f"{target_name}{export_extension}"
        extension = Path(target_name).suffix.lower()
        if allowed_extensions and extension not in allowed_extensions:
            continue
        relative_parent = safe_relative_drive_path(item["drive_path"], folder_name=folder_name)
        target_dir = out_dir / relative_parent
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = unique_path(target_dir / target_name)

        if export_mime:
            request = service.files().export_media(fileId=item["id"], mimeType=export_mime)
        else:
            request = service.files().get_media(fileId=item["id"])
        write_media_request(request=request, target_path=target_path)
        downloaded.append(
            DriveDownloadedFile(
                file_id=item["id"],
                name=item["name"],
                mime_type=item["mimeType"],
                drive_path=item["drive_path"],
                local_path=str(target_path),
                size_bytes=target_path.stat().st_size,
                modified_time=item.get("modifiedTime"),
                web_view_link=item.get("webViewLink"),
            )
        )

    manifest = DriveFolderSyncManifest(
        sync_id=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        created_at=datetime.now(timezone.utc).isoformat(),
        folder_name=folder_name,
        folder_id=resolved_folder_id,
        output_dir=str(out_dir),
        downloaded_count=len(downloaded),
        files=downloaded,
    )
    manifest_path = out_dir / f"drive_manifest_{manifest.sync_id}.json"
    manifest_path.write_text(
        json.dumps(asdict(manifest), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest_path, manifest


def build_drive_service(credentials_file: str | Path):
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError(
            "Missing Google Drive dependencies. Install with: "
            "python3 -m pip install google-api-python-client google-auth"
        ) from exc

    scopes = ["https://www.googleapis.com/auth/drive.readonly"]
    credentials = service_account.Credentials.from_service_account_file(
        str(credentials_file),
        scopes=scopes,
    )
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def find_folder_id(*, service, folder_name: str) -> str:
    escaped = folder_name.replace("\\", "\\\\").replace("'", "\\'")
    response = (
        service.files()
        .list(
            q=(
                f"name = '{escaped}' and "
                f"mimeType = '{DRIVE_FOLDER_MIME}' and trashed = false"
            ),
            fields="files(id, name, webViewLink)",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            pageSize=10,
        )
        .execute()
    )
    files = response.get("files", [])
    if not files:
        raise FileNotFoundError(
            f"Không tìm thấy Google Drive folder '{folder_name}'. "
            "Hãy share folder này cho email service account trong JSON credential."
        )
    if len(files) > 1:
        names = ", ".join(item["id"] for item in files)
        raise RuntimeError(
            f"Tìm thấy nhiều folder tên '{folder_name}'. Chạy lại với --folder-id. IDs: {names}"
        )
    return str(files[0]["id"])


def iter_folder_files(*, service, folder_id: str, parent_path: str, recursive: bool):
    page_token = None
    while True:
        response = (
            service.files()
            .list(
                q=f"'{folder_id}' in parents and trashed = false",
                fields=(
                    "nextPageToken, files(id, name, mimeType, size, modifiedTime, "
                    "webViewLink)"
                ),
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                pageSize=1000,
                pageToken=page_token,
            )
            .execute()
        )
        for item in response.get("files", []):
            drive_path = f"{parent_path}/{item['name']}"
            enriched = {**item, "drive_path": drive_path}
            yield enriched
            if recursive and item["mimeType"] == DRIVE_FOLDER_MIME:
                yield from iter_folder_files(
                    service=service,
                    folder_id=item["id"],
                    parent_path=drive_path,
                    recursive=True,
                )
        page_token = response.get("nextPageToken")
        if not page_token:
            break


def write_media_request(*, request, target_path: Path) -> None:
    from googleapiclient.http import MediaIoBaseDownload

    with target_path.open("wb") as handle:
        downloader = MediaIoBaseDownload(handle, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()


def normalize_extensions(values: Iterable[str] | None) -> set[str]:
    if not values:
        return set()
    normalized: set[str] = set()
    for value in values:
        for part in str(value).split(","):
            token = part.strip().lower()
            if not token:
                continue
            normalized.add(token if token.startswith(".") else f".{token}")
    return normalized


def safe_filename(name: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|]+", "_", name).strip()
    return cleaned or "untitled"


def safe_relative_drive_path(drive_path: str, *, folder_name: str) -> Path:
    parent = Path(drive_path).parent
    parts = list(parent.parts)
    if parts and parts[0] == folder_name:
        parts = parts[1:]
    return Path(*[safe_filename(part) for part in parts]) if parts else Path()


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    for index in range(1, 10_000):
        candidate = path.with_name(f"{stem}_{index}{suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Không tạo được file unique cho {path}")


def guess_data_extensions() -> list[str]:
    return [
        ".csv",
        ".tsv",
        ".xlsx",
        ".xls",
        ".parquet",
        ".json",
        ".jsonl",
        ".feather",
        ".pdf",
        ".txt",
        ".docx",
        ".pptx",
        ".mp3",
        ".mp4",
    ]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Download a Google Drive folder to local data.")
    parser.add_argument("--credentials-file", required=True)
    parser.add_argument("--folder-name", default="Quant Science")
    parser.add_argument("--folder-id", default=None)
    parser.add_argument("--output-dir", default="data/quant_science_drive")
    parser.add_argument(
        "--extensions",
        nargs="*",
        default=guess_data_extensions(),
        help="Allowed extensions. Use --extensions '' to allow all files.",
    )
    parser.add_argument("--no-recursive", action="store_true")
    args = parser.parse_args(argv)

    extensions = None if args.extensions == [""] else args.extensions
    manifest_path, manifest = sync_drive_folder(
        credentials_file=args.credentials_file,
        folder_name=args.folder_name,
        folder_id=args.folder_id,
        output_dir=args.output_dir,
        include_extensions=extensions,
        recursive=not args.no_recursive,
    )
    print(f"Downloaded {manifest.downloaded_count} files")
    print(f"Manifest: {manifest_path}")
    for item in manifest.files:
        mime = item.mime_type or mimetypes.guess_type(item.local_path)[0] or "unknown"
        print(f"- {item.drive_path} -> {item.local_path} ({mime}, {item.size_bytes} bytes)")


if __name__ == "__main__":
    main()
