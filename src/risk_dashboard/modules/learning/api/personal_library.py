"""Private library routes: authenticated account identity on every operation."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.formparsers import MultiPartException

from risk_dashboard.modules.auth.application.dependencies import resolve_principal
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.learning.infrastructure import personal_library as storage
from risk_dashboard.modules.learning.schemas.personal_library import (
    CatalogDocument,
    DocumentMetadata,
    LibraryPatch,
    ReadingEvent,
)

router = APIRouter(prefix="/library", tags=["Learning"])


def _repo():
    return storage.PersonalLibrary()


@router.get("")
def list_library(response: Response, principal: AuthPrincipal = Depends(resolve_principal)):
    response.headers["Cache-Control"] = "private, no-store"
    return _repo().list(principal.account_id)


@router.post("/items")
def save_catalog(req: CatalogDocument, principal: AuthPrincipal = Depends(resolve_principal)):
    return _repo().save_catalog(principal.account_id, req.model_dump())


@router.post("/uploads")
async def upload_document(request: Request, principal: AuthPrincipal = Depends(resolve_principal)):
    # Authenticate before parsing; bound both declared and streamed multipart bodies.
    limit = storage.MAX_UPLOAD_BYTES + 64 * 1024
    length = request.headers.get("content-length", "0")
    if not length.isdecimal():
        raise HTTPException(400, "Kích thước upload không hợp lệ.")
    if int(length) > limit:
        raise HTTPException(413, "Mỗi PDF tối đa 40 MB.")
    received = 0
    overflow = False

    async def bounded_receive():
        nonlocal received, overflow
        message = await request.receive()
        received += len(message.get("body", b""))
        if received > limit:
            overflow = True
            # MultiPartParser closes temporary spools on this exception.
            raise MultiPartException("Mỗi PDF tối đa 40 MB.")
        return message

    bounded = Request(request.scope, receive=bounded_receive)
    try:
        async with bounded.form(max_files=1, max_fields=3, max_part_size=4096) as form:
            if len(form.multi_items()) != len(form) or set(form) - {
                "file",
                "title",
                "author",
                "kind",
            }:
                raise HTTPException(422, "Thông tin upload không hợp lệ.")
            file = form.get("file")
            if (
                not isinstance(file, UploadFile)
                or not (file.filename or "").lower().endswith(".pdf")
                or file.content_type not in {"application/pdf", "application/octet-stream"}
            ):
                raise HTTPException(422, "Chỉ hỗ trợ file PDF. Hãy chọn bản PDF của tài liệu.")
            metadata = DocumentMetadata.model_validate(
                {key: value for key, value in form.items() if key != "file"}
            )
            item, created = await run_in_threadpool(
                _repo().upload, principal.account_id, file.file, metadata.model_dump()
            )
            return JSONResponse(
                item, status_code=201 if created else 200, headers={"Cache-Control": "no-store"}
            )
    except ValidationError as exc:
        raise HTTPException(
            422, "Nhập tên tài liệu (1–240 ký tự) và loại tài liệu hợp lệ."
        ) from exc
    except StarletteHTTPException as exc:
        if overflow:
            raise HTTPException(413, "Mỗi PDF tối đa 40 MB.") from exc
        raise


@router.get("/items/{item_id}")
def get_item(
    item_id: str, response: Response, principal: AuthPrincipal = Depends(resolve_principal)
):
    response.headers["Cache-Control"] = "private, no-store"
    return _repo().get(principal.account_id, item_id)


@router.patch("/items/{item_id}")
def update_item(
    item_id: str, req: LibraryPatch, principal: AuthPrincipal = Depends(resolve_principal)
):
    return _repo().update(principal.account_id, item_id, req.model_dump(exclude_unset=True))


@router.post("/items/{item_id}/open")
def opened(item_id: str, req: ReadingEvent, principal: AuthPrincipal = Depends(resolve_principal)):
    return _repo().opened(principal.account_id, item_id, req.event_id)


@router.get("/items/{item_id}/file.pdf")
def read_file(item_id: str, principal: AuthPrincipal = Depends(resolve_principal)):
    return FileResponse(
        _repo().file_path(principal.account_id, item_id),
        media_type="application/pdf",
        filename="document.pdf",
        content_disposition_type="inline",
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: str, principal: AuthPrincipal = Depends(resolve_principal)):
    _repo().delete(principal.account_id, item_id)
    return Response(status_code=204)
