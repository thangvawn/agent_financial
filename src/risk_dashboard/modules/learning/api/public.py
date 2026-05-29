from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Literal
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Query

from risk_dashboard.app.config.settings import get_settings
from risk_dashboard.modules.ai_assistant.application.services import RespondWithAssistant
from risk_dashboard.modules.ai_assistant.infrastructure.repositories.sqlite import SqliteAssistantConversationRepository
from risk_dashboard.modules.learning.application.services import (
    CompleteLearningLesson,
    GetContextRecommendation,
    GetLearningHome,
    GetLearningLesson,
    SeedLearningHome,
    SubmitLearningQuiz,
)
from risk_dashboard.modules.learning.infrastructure.catalog_reader import SqliteLearningCatalog
from risk_dashboard.modules.learning.infrastructure.repositories.sqlite import SqliteLearningHomeRepository
from risk_dashboard.modules.learning.schemas.requests import (
    LearningCoachRequest,
    LearningQuizSubmitRequest,
    LearningTutorRequest,
)
from risk_dashboard.modules.learning.schemas.responses import (
    LearningAssetItemResponse,
    LearningAssetListResponse,
    LearningCoachResponse,
    LearningContextResponse,
    LearningHomeResponse,
    LearningLessonResponse,
    LearningQuizSubmitResponse,
    LearningTutorResponse,
)

router = APIRouter(prefix="/learning")


def _repo() -> SqliteLearningHomeRepository:
    return SqliteLearningHomeRepository()


def _catalog() -> SqliteLearningCatalog:
    return SqliteLearningCatalog()


def _assistant() -> RespondWithAssistant:
    return RespondWithAssistant(conversations=SqliteAssistantConversationRepository())


VIDEO_EXTENSIONS = {
    ".mp4",
    ".webm",
    ".mov",
    ".m4v",
    ".avi",
    ".mkv",
    ".mpg",
    ".mpeg",
    ".wmv",
    ".flv",
    ".3gp",
}
AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".ogg",
    ".oga",
    ".flac",
    ".opus",
}
BOOK_EXTENSIONS = {".pdf", ".epub", ".mobi", ".txt", ".docx"}
COVER_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")


@router.get("/assets", response_model=LearningAssetListResponse, tags=["Learning"])
def list_learning_assets(kind: Literal["videos", "books", "audios"] = Query(default="videos")) -> LearningAssetListResponse:
    settings = get_settings()
    base_dir = settings.learning_assets_dir / kind
    image_dir = settings.learning_assets_dir / "images"
    if not base_dir.exists():
        if kind not in {"videos", "audios"}:
            return LearningAssetListResponse(kind=kind, items=[])
    extensions = (
        BOOK_EXTENSIONS
        if kind == "books"
        else AUDIO_EXTENSIONS
        if kind == "audios"
        else (VIDEO_EXTENSIONS | AUDIO_EXTENSIONS)
    )
    source_dirs = (
        [settings.learning_assets_dir / "videos", settings.learning_assets_dir / "audios"]
        if kind == "videos"
        else [settings.learning_assets_dir / "audios", settings.learning_assets_dir / "videos"]
        if kind == "audios"
        else [settings.learning_assets_dir / "books"]
    )
    items: list[LearningAssetItemResponse] = []

    for directory in source_dirs:
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*"), key=lambda item: str(item.relative_to(directory)).lower()):
            if not path.is_file() or path.name.startswith("."):
                continue
            if path.suffix.lower() not in extensions:
                continue
            relative_path = path.relative_to(settings.learning_assets_dir)
            asset_id = _slugify(str(relative_path.with_suffix("")))
            mime_type, _ = mimetypes.guess_type(path.name)
            cover_url = _find_cover_url(image_dir=image_dir, stem=path.stem)
            items.append(
                LearningAssetItemResponse(
                    asset_id=asset_id,
                    kind=kind,
                    file_name=path.name,
                    title=_title_from_stem(path.stem),
                    url=f"/learning-assets/{_quote_path(relative_path)}",
                    mime_type=mime_type,
                    size_bytes=path.stat().st_size,
                    cover_url=cover_url,
                )
            )
    return LearningAssetListResponse(kind=kind, items=items)


@router.get("/home", response_model=LearningHomeResponse, tags=["Learning"])
def get_learning_home(session_id: str = Query(..., min_length=8)) -> LearningHomeResponse:
    try:
        repo = _repo()
        service = GetLearningHome(reader=repo, catalog=_catalog(), progress=repo)
        return service.execute(user_id=session_id)
    except KeyError as exc:
        # Saved home state references a deleted path/lesson — fall through to reseed.
        pass
    except ValueError as exc:
        # Graceful bootstrap for local/public sessions that skipped onboarding seeding.
        if str(exc) != "Learning home state not found.":
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    try:
        SeedLearningHome(writer=_repo(), catalog=_catalog()).execute(
            user_id=session_id,
            persona_segment="starter",
            primary_route="learn",
        )
        repo = _repo()
        return GetLearningHome(reader=repo, catalog=_catalog(), progress=repo).execute(user_id=session_id)
    except Exception as seed_exc:  # pragma: no cover - defensive fallback
        raise HTTPException(status_code=404, detail=str(seed_exc)) from seed_exc


@router.get("/lessons/{lesson_id}", response_model=LearningLessonResponse, tags=["Learning"])
def get_learning_lesson(lesson_id: str, session_id: str = Query(..., min_length=8)) -> LearningLessonResponse:
    try:
        return GetLearningLesson(catalog=_catalog(), progress=_repo()).execute(
            user_id=session_id,
            lesson_id=lesson_id,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Lesson not found.") from exc


@router.post("/lessons/{lesson_id}/quiz", response_model=LearningQuizSubmitResponse, tags=["Learning"])
def submit_learning_quiz(lesson_id: str, req: LearningQuizSubmitRequest) -> LearningQuizSubmitResponse:
    try:
        return SubmitLearningQuiz(
            catalog=_catalog(),
            progress=_repo(),
            home_reader=_repo(),
            home_writer=_repo(),
        ).execute(user_id=req.session_id, lesson_id=lesson_id, answers=req.answers)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Lesson not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/lessons/{lesson_id}/complete", response_model=LearningLessonResponse, tags=["Learning"])
def complete_learning_lesson(lesson_id: str, session_id: str = Query(..., min_length=8)) -> LearningLessonResponse:
    try:
        return CompleteLearningLesson(
            catalog=_catalog(),
            progress=_repo(),
            home_reader=_repo(),
            home_writer=_repo(),
        ).execute(user_id=session_id, lesson_id=lesson_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Lesson not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/tutor", response_model=LearningTutorResponse, tags=["Learning"])
def learning_tutor(req: LearningTutorRequest) -> LearningTutorResponse:
    try:
        reply = _assistant().execute(
            session_id=req.session_id,
            surface="learning",
            prompt=req.question,
            role_hint="tutor",
            lesson_id=req.lesson_id,
            knowledge_level=req.knowledge_level,
        )
        return LearningTutorResponse(
            lesson_id=req.lesson_id,
            summary=reply.summary,
            explanation=reply.explanation,
            check_question=reply.check_question or "Ban se dien dat lai bai nay the nao?",
            next_lesson_hint=reply.next_step,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Lesson not found.") from exc


@router.post("/coach", response_model=LearningCoachResponse, tags=["Learning"])
def learning_coach(req: LearningCoachRequest) -> LearningCoachResponse:
    try:
        reply = _assistant().execute(
            session_id=req.session_id,
            surface="learning",
            prompt="",
            role_hint="coach",
            trigger=req.trigger,
        )
        return LearningCoachResponse(
            nudge_type=req.trigger,
            title=reply.title,
            message=reply.explanation,
            cta_label=reply.next_step,
            cta_path=reply.cta_path,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/context", response_model=LearningContextResponse, tags=["Learning"])
def learning_context(trigger: str = Query(..., min_length=3, max_length=100)) -> LearningContextResponse:
    try:
        return GetContextRecommendation(catalog=_catalog()).execute(trigger=trigger)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Context lesson not found.") from exc


CatalogKind = Literal["video", "book", "paper", "course"]


@router.get("/catalog", tags=["Learning"])
def learning_catalog(
    kind: CatalogKind = Query(default="video"),
    topic: str | None = Query(default=None, max_length=64),
    tier: str | None = Query(default=None, max_length=48),
    language: str | None = Query(default=None, max_length=8),
    limit: int = Query(default=60, ge=1, le=200),
) -> dict:
    """Return curated resources from `learning_{videos|books|papers|courses}`.

    Catalog tables are populated by `risk-learning-crawl`; if they're empty
    (e.g. before first crawl) the response is `{"kind": kind, "items": []}`.
    """
    from risk_dashboard.modules.learning.crawlers.common import open_catalog_db  # type: ignore[import-not-found]

    table = {
        "video": "learning_videos",
        "book": "learning_books",
        "paper": "learning_papers",
        "course": "learning_courses",
    }[kind]

    where: list[str] = ["is_active = 1"]
    params: list[object] = []
    if topic:
        where.append(f"EXISTS (SELECT 1 FROM learning_resource_topics rt "
                     f"WHERE rt.resource_kind = ? AND rt.resource_id = {table}.{kind}_id "
                     f"AND rt.topic_id = ?)")
        params.extend([kind, topic])
    if tier:
        where.append("tier = ?")
        params.append(tier)
    if language:
        where.append("language = ?")
        params.append(language)

    sort = "published_at" if kind == "paper" else "fetched_at"
    query = (
        f"SELECT * FROM {table} WHERE {' AND '.join(where)} "
        f"ORDER BY {sort} DESC NULLS LAST LIMIT ?"
    )
    params.append(limit)

    import sqlite3 as _sqlite3
    try:
        conn = open_catalog_db()
    except _sqlite3.DatabaseError:
        return {"kind": kind, "items": [], "count": 0, "warning": "catalog_db_unavailable"}
    try:
        rows = [dict(row) for row in conn.execute(query, params).fetchall()]
    except _sqlite3.DatabaseError:
        rows = []
    finally:
        conn.close()

    import json as _json
    for row in rows:
        if isinstance(row.get("topics_json"), str):
            try:
                row["topics"] = _json.loads(row.pop("topics_json"))
            except _json.JSONDecodeError:
                row["topics"] = []
        if "authors_json" in row and isinstance(row["authors_json"], str):
            try:
                row["authors"] = _json.loads(row.pop("authors_json"))
            except _json.JSONDecodeError:
                row["authors"] = []
    return {"kind": kind, "items": rows, "count": len(rows)}


@router.get("/catalog/topics", tags=["Learning"])
def learning_catalog_topics() -> dict:
    """List topic taxonomy + counts per topic."""
    from risk_dashboard.modules.learning.crawlers.common import open_catalog_db  # type: ignore[import-not-found]

    import sqlite3 as _sqlite3
    try:
        conn = open_catalog_db()
    except _sqlite3.DatabaseError:
        return {"topics": [], "warning": "catalog_db_unavailable"}
    try:
        topics = [dict(r) for r in conn.execute(
            "SELECT topic_id, label_vi, label_en, tier, description, sort_order "
            "FROM learning_topics ORDER BY sort_order"
        ).fetchall()]
        counts = {row["topic_id"]: row["n"] for row in conn.execute(
            "SELECT topic_id, COUNT(*) as n FROM learning_resource_topics GROUP BY topic_id"
        ).fetchall()}
    except _sqlite3.DatabaseError:
        topics, counts = [], {}
    finally:
        conn.close()
    for topic in topics:
        topic["resource_count"] = counts.get(topic["topic_id"], 0)
    return {"topics": topics}


def _title_from_stem(stem: str) -> str:
    parts = [part for part in stem.replace("_", " ").replace("-", " ").split(" ") if part]
    if not parts:
        return "Untitled asset"
    return " ".join(part.capitalize() for part in parts)


def _slugify(text: str) -> str:
    normalized = "".join(char.lower() if char.isalnum() else "-" for char in text)
    return "-".join(part for part in normalized.split("-") if part)


def _quote_path(path: Path) -> str:
    return "/".join(quote(part) for part in path.parts)


def _find_cover_url(*, image_dir: Path, stem: str) -> str | None:
    if not image_dir.exists():
        return None
    target_slug = _slugify(stem)
    for extension in COVER_EXTENSIONS:
        candidate = image_dir / f"{stem}{extension}"
        if candidate.exists() and candidate.is_file():
            return f"/learning-assets/images/{quote(candidate.name)}"
    for path in image_dir.glob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in COVER_EXTENSIONS:
            continue
        if _slugify(path.stem) == target_slug:
            return f"/learning-assets/images/{quote(path.name)}"
    return None
