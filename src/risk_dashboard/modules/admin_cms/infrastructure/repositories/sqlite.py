from __future__ import annotations

import json
import uuid

from risk_dashboard.modules.admin_cms.domain.entities import (
    CmsAiGenerationLog,
    CmsContentItem,
    CmsContentVersion,
    CmsPublishEvent,
    CmsReviewTask,
)
from risk_dashboard.platform.database import open_app_state_db, reset_app_state_tables


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class SqliteAdminCmsRepository:
    def save_item(self, item: CmsContentItem) -> CmsContentItem:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO cms_content_items (
                  content_id, content_type, slug, title, locale, owner_team, risk_category,
                  workflow_state, current_version, published_version, created_by, updated_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(content_id) DO UPDATE SET
                  content_type = excluded.content_type,
                  slug = excluded.slug,
                  title = excluded.title,
                  locale = excluded.locale,
                  owner_team = excluded.owner_team,
                  risk_category = excluded.risk_category,
                  workflow_state = excluded.workflow_state,
                  current_version = excluded.current_version,
                  published_version = excluded.published_version,
                  updated_by = excluded.updated_by,
                  updated_at = excluded.updated_at
                """,
                (
                    item.content_id,
                    item.content_type,
                    item.slug,
                    item.title,
                    item.locale,
                    item.owner_team,
                    item.risk_category,
                    item.workflow_state,
                    item.current_version,
                    item.published_version,
                    item.created_by,
                    item.updated_by,
                    item.created_at,
                    item.updated_at,
                ),
            )
            conn.commit()
        return item

    def get_item(self, *, content_id: str) -> CmsContentItem | None:
        with open_app_state_db() as conn:
            row = conn.execute("SELECT * FROM cms_content_items WHERE content_id = ?", (content_id,)).fetchone()
        if row is None:
            return None
        return CmsContentItem(**dict(row))

    def list_items(self, *, content_type: str | None = None) -> list[CmsContentItem]:
        with open_app_state_db() as conn:
            if content_type:
                rows = conn.execute(
                    "SELECT * FROM cms_content_items WHERE content_type = ? ORDER BY updated_at DESC",
                    (content_type,),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM cms_content_items ORDER BY updated_at DESC").fetchall()
        return [CmsContentItem(**dict(row)) for row in rows]

    def list_published_content(self, *, content_type: str) -> list[tuple[CmsContentItem, CmsContentVersion]]:
        items = [
            item
            for item in self.list_items(content_type=content_type)
            if item.workflow_state == "published" and item.published_version is not None
        ]
        published: list[tuple[CmsContentItem, CmsContentVersion]] = []
        for item in items:
            version = self.get_version(content_id=item.content_id, version_number=int(item.published_version or 0))
            if version is None or version.status != "published":
                continue
            published.append((item, version))
        return published

    def find_published_content(self, *, content_type: str, slug: str) -> tuple[CmsContentItem, CmsContentVersion] | None:
        normalized_slug = slug.strip()
        for item, version in self.list_published_content(content_type=content_type):
            if item.slug == normalized_slug:
                return item, version
        return None

    def save_version(self, version: CmsContentVersion) -> CmsContentVersion:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO cms_content_versions (
                  version_id, content_id, version_number, payload_json, status, origin, change_summary,
                  created_by, reviewed_by, compliance_reviewed_by, published_by, created_at, published_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(version_id) DO UPDATE SET
                  payload_json = excluded.payload_json,
                  status = excluded.status,
                  origin = excluded.origin,
                  change_summary = excluded.change_summary,
                  reviewed_by = excluded.reviewed_by,
                  compliance_reviewed_by = excluded.compliance_reviewed_by,
                  published_by = excluded.published_by,
                  published_at = excluded.published_at
                """,
                (
                    version.version_id,
                    version.content_id,
                    version.version_number,
                    json.dumps(version.payload, ensure_ascii=False),
                    version.status,
                    version.origin,
                    version.change_summary,
                    version.created_by,
                    version.reviewed_by,
                    version.compliance_reviewed_by,
                    version.published_by,
                    version.created_at,
                    version.published_at,
                ),
            )
            conn.commit()
        return version

    def list_versions(self, *, content_id: str) -> list[CmsContentVersion]:
        with open_app_state_db() as conn:
            rows = conn.execute(
                "SELECT * FROM cms_content_versions WHERE content_id = ? ORDER BY version_number DESC",
                (content_id,),
            ).fetchall()
        return [
            CmsContentVersion(
                version_id=row["version_id"],
                content_id=row["content_id"],
                version_number=row["version_number"],
                payload=json.loads(row["payload_json"] or "{}"),
                status=row["status"],
                origin=row["origin"],
                change_summary=row["change_summary"],
                created_by=row["created_by"],
                reviewed_by=row["reviewed_by"],
                compliance_reviewed_by=row["compliance_reviewed_by"],
                published_by=row["published_by"],
                created_at=row["created_at"],
                published_at=row["published_at"],
            )
            for row in rows
        ]

    def get_version(self, *, content_id: str, version_number: int) -> CmsContentVersion | None:
        versions = self.list_versions(content_id=content_id)
        return next((item for item in versions if item.version_number == version_number), None)

    def save_review_task(self, task: CmsReviewTask) -> CmsReviewTask:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO cms_review_tasks (
                  task_id, content_id, version_number, review_type, assignee_role, status,
                  created_by, reviewer_id, comments, created_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.task_id,
                    task.content_id,
                    task.version_number,
                    task.review_type,
                    task.assignee_role,
                    task.status,
                    task.created_by,
                    task.reviewer_id,
                    task.comments,
                    task.created_at,
                    task.completed_at,
                ),
            )
            conn.commit()
        return task

    def list_review_tasks(self, *, status: str | None = None) -> list[CmsReviewTask]:
        with open_app_state_db() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM cms_review_tasks WHERE status = ? ORDER BY created_at DESC",
                    (status,),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM cms_review_tasks ORDER BY created_at DESC").fetchall()
        return [CmsReviewTask(**dict(row)) for row in rows]

    def complete_review_task(self, *, content_id: str, reviewer_id: str, comments: str | None = None) -> None:
        with open_app_state_db() as conn:
            conn.execute(
                """
                UPDATE cms_review_tasks
                SET status = 'completed', reviewer_id = ?, comments = ?, completed_at = datetime('now')
                WHERE content_id = ? AND status = 'pending'
                """,
                (reviewer_id, comments, content_id),
            )
            conn.commit()

    def save_publish_event(self, event: CmsPublishEvent) -> CmsPublishEvent:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO cms_publish_events (
                  event_id, content_id, version_number, action, actor_role, actor_id, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.content_id,
                    event.version_number,
                    event.action,
                    event.actor_role,
                    event.actor_id,
                    event.notes,
                    event.created_at,
                ),
            )
            conn.commit()
        return event

    def save_ai_generation_log(self, log: CmsAiGenerationLog) -> CmsAiGenerationLog:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO cms_ai_generation_logs (
                  generation_id, content_type, content_id, prompt_version, model_name,
                  input_summary, output_summary, created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log.generation_id,
                    log.content_type,
                    log.content_id,
                    log.prompt_version,
                    log.model_name,
                    log.input_summary,
                    log.output_summary,
                    log.created_by,
                    log.created_at,
                ),
            )
            conn.commit()
        return log

    def get_analytics(self, *, content_id: str) -> dict[str, object]:
        with open_app_state_db() as conn:
            row = conn.execute(
                "SELECT * FROM cms_analytics_snapshots WHERE content_id = ?",
                (content_id,),
            ).fetchone()
        if row is None:
            return {
                "content_id": content_id,
                "impression_count": 0,
                "open_count": 0,
                "completion_count": 0,
                "clickthrough_count": 0,
                "last_event_at": None,
            }
        return dict(row)

    def upsert_analytics(self, *, content_id: str, event_type: str, occurred_at: str) -> dict[str, object]:
        field_map = {
            "impression": "impression_count",
            "open": "open_count",
            "completion": "completion_count",
            "clickthrough": "clickthrough_count",
        }
        target_field = field_map.get(event_type)
        if target_field is None:
            raise ValueError("event_type khong hop le.")
        with open_app_state_db() as conn:
            existing = conn.execute(
                "SELECT * FROM cms_analytics_snapshots WHERE content_id = ?",
                (content_id,),
            ).fetchone()
            if existing is None:
                conn.execute(
                    """
                    INSERT INTO cms_analytics_snapshots (
                      content_id, impression_count, open_count, completion_count, clickthrough_count, last_event_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        content_id,
                        1 if target_field == "impression_count" else 0,
                        1 if target_field == "open_count" else 0,
                        1 if target_field == "completion_count" else 0,
                        1 if target_field == "clickthrough_count" else 0,
                        occurred_at,
                    ),
                )
            else:
                conn.execute(
                    f"UPDATE cms_analytics_snapshots SET {target_field} = {target_field} + 1, last_event_at = ? WHERE content_id = ?",
                    (occurred_at, content_id),
                )
            conn.commit()
        return self.get_analytics(content_id=content_id)

    def analytics_overview(self) -> dict[str, object]:
        with open_app_state_db() as conn:
            counts = conn.execute(
                "SELECT content_type, COUNT(*) AS item_count FROM cms_content_items GROUP BY content_type ORDER BY content_type ASC"
            ).fetchall()
            pending_review = conn.execute(
                "SELECT COUNT(*) AS total FROM cms_review_tasks WHERE status = 'pending'"
            ).fetchone()
        return {
            "content_counts": {row["content_type"]: row["item_count"] for row in counts},
            "pending_review_count": pending_review["total"] if pending_review else 0,
        }


def new_content_id(content_type: str) -> str:
    return _new_id(f"cms_{content_type}")


def new_version_id() -> str:
    return _new_id("cmsver")


def new_review_task_id() -> str:
    return _new_id("cmsrev")


def new_publish_event_id() -> str:
    return _new_id("cmspub")


def new_ai_generation_id() -> str:
    return _new_id("cmsai")


def reset_admin_cms_state() -> None:
    reset_app_state_tables()
