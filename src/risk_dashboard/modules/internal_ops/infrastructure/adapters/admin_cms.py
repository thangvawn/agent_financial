from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any

from risk_dashboard.modules.admin_cms.application.services import (
    GetContentDetail,
    ListContent,
    ListContentVersions,
    ListReviewQueue,
)
from risk_dashboard.modules.admin_cms.infrastructure.repositories.sqlite import (
    SqliteAdminCmsRepository,
)
from risk_dashboard.modules.internal_ops.application.policy import PolicyEngine, PurposeGrant
from risk_dashboard.modules.internal_ops.application.redaction import RedactionEngine
from risk_dashboard.modules.internal_ops.domain.contracts import (
    EvidenceBatch,
    EvidenceItem,
    EvidenceRef,
)

logger = logging.getLogger(__name__)

CMS_CONTENT_ALLOWLIST = {
    "content_id", "content_type", "title", "status",
    "version", "updated_at", "summary", "body", "author",
}
CMS_VERSION_ALLOWLIST = {
    "version_id", "content_id", "version", "status",
    "created_at", "change_summary",
}
CMS_QUEUE_ALLOWLIST = {
    "task_id", "content_id", "stage", "status",
    "assigned_role", "created_at",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _item_from_obj(
    obj: Any,
    allowlist: set[str],
    res_type: str,
    id_key: str,
    date_key: str,
    default_id: str,
    now_iso: str,
) -> EvidenceItem:
    raw = obj.model_dump() if hasattr(obj, "model_dump") else dict(obj)
    clean, reds = RedactionEngine.filter_and_redact_dict(raw, allowlist)
    return EvidenceItem(
        ref=EvidenceRef(
            source_module="admin_cms",
            resource_type=res_type,
            resource_id=str(clean.get(id_key, default_id)),
            observed_at=str(clean.get(date_key, now_iso)),
        ),
        classification="metadata",
        fields=clean,
        redactions=tuple(reds),
    )


class AdminCmsAdapter:
    """Direct in-process adapter to Admin CMS read services. Zero HTTP loopback."""

    def __init__(
        self,
        list_content_svc: ListContent | None = None,
        get_detail_svc: GetContentDetail | None = None,
        list_versions_svc: ListContentVersions | None = None,
        list_queue_svc: ListReviewQueue | None = None,
    ) -> None:
        repo = SqliteAdminCmsRepository()
        self._list_content = list_content_svc or ListContent(repo=repo)
        self._get_detail = get_detail_svc or GetContentDetail(repo=repo)
        self._list_versions = list_versions_svc or ListContentVersions(repo=repo)
        self._list_queue = list_queue_svc or ListReviewQueue(repo=repo)

    def get_content_context(
        self,
        grant: PurposeGrant,
        content_id: str | None = None,
        content_type: str | None = None,
    ) -> EvidenceBatch:
        PolicyEngine.authorize_tool_call(grant, "ops.get_content_context@1.0.0", "admin_cms")
        now_iso = _utc_now_iso()
        items: list[EvidenceItem] = []

        if content_id:
            try:
                detail = self._get_detail.execute(content_id=content_id)
                items.append(_item_from_obj(detail, CMS_CONTENT_ALLOWLIST, "cms_content", "content_id", "updated_at", content_id, now_iso))
            except Exception as exc:
                logger.warning("Failed to fetch CMS content detail for %s: %s", content_id, exc)

            try:
                for ver in self._list_versions.execute(content_id=content_id):
                    items.append(_item_from_obj(ver, CMS_VERSION_ALLOWLIST, "cms_version", "version_id", "created_at", "v1", now_iso))
            except Exception as exc:
                logger.warning("Failed to fetch CMS versions for %s: %s", content_id, exc)

            try:
                for task in self._list_queue.execute():
                    raw = task.model_dump() if hasattr(task, "model_dump") else dict(task)
                    if raw.get("content_id") == content_id:
                        items.append(_item_from_obj(task, CMS_QUEUE_ALLOWLIST, "cms_review_task", "task_id", "created_at", "task", now_iso))
            except Exception as exc:
                logger.warning("Failed to fetch CMS review queue for %s: %s", content_id, exc)
        else:
            try:
                for c in self._list_content.execute(content_type=content_type)[:50]:
                    items.append(_item_from_obj(c, CMS_CONTENT_ALLOWLIST, "cms_content", "content_id", "updated_at", "content", now_iso))
            except Exception as exc:
                logger.warning("Failed to list CMS content: %s", exc)

            try:
                for task in self._list_queue.execute()[:20]:
                    items.append(_item_from_obj(task, CMS_QUEUE_ALLOWLIST, "cms_review_task", "task_id", "created_at", "task", now_iso))
            except Exception as exc:
                logger.warning("Failed to list CMS review queue: %s", exc)

        return EvidenceBatch(
            items=tuple(items),
            source_module="admin_cms",
            fetched_at=now_iso,
            status="available",
        )


