from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/learning-cms", tags=["Learning CMS (Retired)"])

RETIREMENT_DETAIL = (
    "Learning CMS legacy đã được retire khỏi runtime vận hành. "
    "Hãy dùng Content Ops Admin cho lesson/course/path/glossary/explainer/nudge/disclaimer."
)


def _retired() -> HTTPException:
    return HTTPException(
        status_code=410,
        detail=RETIREMENT_DETAIL,
        headers={"X-Legacy-Learning-Cms": "retired", "X-Primary-Admin-Surface": "content_ops_admin"},
    )


@router.api_route("", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@router.api_route("/{legacy_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def retired_learning_cms(_: Request, legacy_path: str = ""):
    raise _retired()
