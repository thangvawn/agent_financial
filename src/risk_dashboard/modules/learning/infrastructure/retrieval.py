from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass
from typing import Sequence

from risk_dashboard.modules.learning.domain.entities import LearningLesson
from risk_dashboard.modules.learning.domain.ports import LearningCatalogReader
from risk_dashboard.modules.learning.infrastructure.catalog_reader import SqliteLearningCatalog
from risk_dashboard.modules.learning.schemas.agent_tools import SourceRef
from risk_dashboard.platform.database import open_app_state_db

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ContentChunk:
    chunk_id: str
    lesson_id: str
    section_id: str
    title: str
    content: str
    source_id: str
    content_version: str
    is_published: bool


# Basic sanitization to neutralize prompt injection phrases in retrieved content
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"system\s+prompt\s*:", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a\b", re.IGNORECASE),
]

DANGEROUS_TAGS_PATTERN = re.compile(
    r"<\s*(script|iframe|object|embed)\b[^>]*>.*?<\s*/\s*\1\s*>|<\s*(script|iframe|object|embed)\b[^>]*/>",
    re.IGNORECASE | re.DOTALL,
)
EVENT_HANDLERS_PATTERN = re.compile(r"\bon\w+\s*=", re.IGNORECASE)


def sanitize_content(text: str) -> str:
    """Neutralize potential prompt injection and unsafe script tags while preserving math and code blocks."""
    clean = text
    # 1. Neutralize injection command patterns
    for pat in INJECTION_PATTERNS:
        clean = pat.sub("[REDACTED_UNSAFE_INSTRUCTION]", clean)

    # 2. Strip dangerous executable tags
    clean = DANGEROUS_TAGS_PATTERN.sub("", clean)

    # 3. Strip inline event handlers
    clean = EVENT_HANDLERS_PATTERN.sub("", clean)

    return clean.strip()


def remove_accents(text: str) -> str:
    """Normalize and remove Vietnamese diacritics for robust matching."""
    nfkd = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    return stripped.replace("đ", "d").replace("Đ", "D")


class LessonChunker:
    @staticmethod
    def chunk_lesson(lesson: LearningLesson, *, content_version: str = "1.0.0") -> list[ContentChunk]:
        """Split lesson body into clean, identifiable sections for retrieval."""
        if lesson.status != "published":
            return []

        chunks: list[ContentChunk] = []
        source_id = f"lesson:{lesson.lesson_id}"

        for idx, paragraph in enumerate(lesson.body):
            section_id = f"sec_{idx + 1}"
            clean_text = sanitize_content(paragraph.strip())
            if not clean_text:
                continue

            chunk_id = f"{lesson.lesson_id}:{section_id}"
            chunks.append(
                ContentChunk(
                    chunk_id=chunk_id,
                    lesson_id=lesson.lesson_id,
                    section_id=section_id,
                    title=lesson.title,
                    content=clean_text,
                    source_id=source_id,
                    content_version=content_version,
                    is_published=True,
                )
            )

        return chunks


class LearningRetrievalIndex:
    def __init__(self, catalog: LearningCatalogReader | None = None) -> None:
        self.catalog = catalog or SqliteLearningCatalog()

    def rebuild_index(self) -> int:
        """Derived index rebuildable from published catalog. Deleted/unpublished items are excluded."""
        lessons = self.catalog.list_lessons()
        total_chunks = 0

        with open_app_state_db() as conn:
            conn.execute("DELETE FROM learning_fts_index")
            for lesson in lessons:
                if lesson.status != "published":
                    continue
                chunks = LessonChunker.chunk_lesson(lesson)
                for c in chunks:
                    conn.execute(
                        """
                        INSERT INTO learning_fts_index (
                            lesson_id, section_id, source_id, content_version, title, content
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (c.lesson_id, c.section_id, c.source_id, c.content_version, c.title, c.content),
                    )
                    total_chunks += 1
            conn.commit()

        return total_chunks

    def search(self, query: str, *, limit: int = 5) -> list[ContentChunk]:
        """Search published curriculum text via FTS5 with normalized LIKE fallback."""
        if not query.strip():
            return []

        clean_query = query.strip()
        unaccented_query = remove_accents(clean_query)
        results: list[ContentChunk] = []

        with open_app_state_db() as conn:
            count_row = conn.execute("SELECT count(*) as cnt FROM learning_fts_index").fetchone()
            if not count_row or count_row["cnt"] == 0:
                self.rebuild_index()

            rows = []
            # Try FTS MATCH on both clean query and unaccented query
            for q_term in [clean_query, unaccented_query]:
                try:
                    fts_query = ' '.join(f'"{word}"' for word in q_term.split() if word.isalnum())
                    if fts_query:
                        matched = conn.execute(
                            """
                            SELECT lesson_id, section_id, source_id, content_version, title, content
                            FROM learning_fts_index
                            WHERE learning_fts_index MATCH ?
                            LIMIT ?
                            """,
                            (fts_query, limit),
                        ).fetchall()
                        if matched:
                            rows.extend(matched)
                            break
                except Exception as exc:
                    logger.debug(f"FTS match failed: {exc}")

            if not rows:
                # Fallback to LIKE substring match with both forms
                rows = conn.execute(
                    """
                    SELECT lesson_id, section_id, source_id, content_version, title, content
                    FROM learning_fts_index
                    WHERE title LIKE ? OR content LIKE ?
                       OR title LIKE ? OR content LIKE ?
                    LIMIT ?
                    """,
                    (
                        f"%{clean_query}%",
                        f"%{clean_query}%",
                        f"%{unaccented_query}%",
                        f"%{unaccented_query}%",
                        limit,
                    ),
                ).fetchall()

            seen_ids = set()
            for row in rows:
                chunk_id = f"{row['lesson_id']}:{row['section_id']}"
                if chunk_id not in seen_ids:
                    seen_ids.add(chunk_id)
                    results.append(
                        ContentChunk(
                            chunk_id=chunk_id,
                            lesson_id=row["lesson_id"],
                            section_id=row["section_id"],
                            title=row["title"],
                            content=row["content"],
                            source_id=row["source_id"],
                            content_version=row["content_version"],
                            is_published=True,
                        )
                    )

        return results[:limit]

    def get_source_refs(self, chunks: Sequence[ContentChunk]) -> tuple[SourceRef, ...]:
        """Extract unique provenance citations from chunks."""
        seen = set()
        refs: list[SourceRef] = []
        for c in chunks:
            key = (c.source_id, c.content_version, c.section_id)
            if key not in seen:
                seen.add(key)
                refs.append(
                    SourceRef(
                        source_id=c.source_id,
                        content_version=c.content_version,
                        section_id=c.section_id,
                    )
                )
        return tuple(refs)

