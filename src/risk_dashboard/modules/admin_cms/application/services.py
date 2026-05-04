from __future__ import annotations

from dataclasses import replace

from risk_dashboard.modules.admin_cms.domain.entities import (
    CmsAiGenerationLog,
    CmsContentItem,
    CmsContentVersion,
    CmsPublishEvent,
    CmsReviewTask,
    utc_now_iso,
)
from risk_dashboard.modules.admin_cms.domain.policies import (
    VALID_CONTENT_TYPES,
    VALID_ROLES,
    VALID_WORKFLOW_STATES,
    can_approve,
    can_archive,
    can_edit,
    can_publish,
    can_submit_review,
    next_review_type,
    role_permissions,
)
from risk_dashboard.modules.admin_cms.infrastructure.repositories.sqlite import (
    SqliteAdminCmsRepository,
    new_ai_generation_id,
    new_content_id,
    new_publish_event_id,
    new_review_task_id,
    new_version_id,
)
from risk_dashboard.modules.admin_cms.schemas.responses import (
    CmsAnalyticsResponse,
    CmsContentResponse,
    CmsContentVersionResponse,
    CmsReviewTaskResponse,
    CmsStatusResponse,
)
from risk_dashboard.modules.trust_safety.application.services import TrustSafetyService


def _ensure_role(role: str) -> str:
    normalized = role.strip().lower()
    if normalized not in VALID_ROLES:
        raise ValueError("Role khong hop le cho Content Ops.")
    return normalized


class GetCmsStatus:
    def __init__(self, repo: SqliteAdminCmsRepository) -> None:
        self.repo = repo

    def execute(self, *, actor_role: str, enabled: bool) -> CmsStatusResponse:
        role = _ensure_role(actor_role)
        return CmsStatusResponse(
            enabled=enabled,
            actor_role=role,
            permissions=role_permissions(role),
            supported_content_types=sorted(VALID_CONTENT_TYPES),
            workflow_states=sorted(VALID_WORKFLOW_STATES),
            analytics_overview=self.repo.analytics_overview(),
        )


class UpsertContentDraft:
    def __init__(self, repo: SqliteAdminCmsRepository) -> None:
        self.repo = repo

    def execute(
        self,
        *,
        content_type: str,
        content_id: str | None,
        slug: str,
        title: str,
        locale: str,
        owner_team: str,
        risk_category: str,
        payload: dict[str, object],
        change_summary: str | None,
        actor_role: str,
        actor_id: str,
        origin: str = "human",
    ) -> CmsContentResponse:
        role = _ensure_role(actor_role)
        if content_type not in VALID_CONTENT_TYPES:
            raise ValueError("content_type khong duoc ho tro.")
        if not can_edit(role=role, content_type=content_type):
            raise ValueError("Role hien tai khong duoc sua content type nay.")
        existing = self.repo.get_item(content_id=content_id) if content_id else None
        now = utc_now_iso()
        item = CmsContentItem(
            content_id=content_id or new_content_id(content_type),
            content_type=content_type,
            slug=slug.strip(),
            title=title.strip(),
            locale=locale.strip(),
            owner_team=owner_team.strip(),
            risk_category=risk_category.strip(),
            workflow_state="draft",
            current_version=(existing.current_version + 1) if existing else 1,
            published_version=existing.published_version if existing else None,
            created_by=existing.created_by if existing else actor_id,
            updated_by=actor_id,
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        version = CmsContentVersion(
            version_id=new_version_id(),
            content_id=item.content_id,
            version_number=item.current_version,
            payload=payload,
            status="draft",
            origin=origin,
            change_summary=change_summary,
            created_by=actor_id,
            created_at=now,
        )
        self.repo.save_item(item)
        self.repo.save_version(version)
        if origin == "ai_assisted":
            self.repo.save_ai_generation_log(
                CmsAiGenerationLog(
                    generation_id=new_ai_generation_id(),
                    content_type=content_type,
                    content_id=item.content_id,
                    prompt_version="cms_ai_draft_v1",
                    model_name="rule-based-draft",
                    input_summary=change_summary or title,
                    output_summary=title,
                    created_by=actor_id,
                )
            )
        return _to_content_response(item, version)


class SubmitContentForReview:
    def __init__(self, repo: SqliteAdminCmsRepository) -> None:
        self.repo = repo

    def execute(self, *, content_id: str, actor_role: str, actor_id: str, comments: str | None) -> CmsContentResponse:
        role = _ensure_role(actor_role)
        item = self.repo.get_item(content_id=content_id)
        if item is None:
            raise ValueError("Khong tim thay content.")
        if not can_submit_review(role=role, content_type=item.content_type):
            raise ValueError("Role hien tai khong duoc submit review.")
        updated = replace(item, workflow_state="review", updated_by=actor_id, updated_at=utc_now_iso())
        self.repo.save_item(updated)
        self.repo.save_review_task(
            CmsReviewTask(
                task_id=new_review_task_id(),
                content_id=content_id,
                version_number=updated.current_version,
                review_type=next_review_type(content_type=item.content_type, risk_category=item.risk_category),
                assignee_role=(
                    "compliance_reviewer"
                    if next_review_type(content_type=item.content_type, risk_category=item.risk_category) == "compliance"
                    else ("moderator" if item.content_type == "community_policy_snippet" else "reviewer")
                ),
                status="pending",
                created_by=actor_id,
                comments=comments,
            )
        )
        version = self.repo.get_version(content_id=content_id, version_number=updated.current_version)
        return _to_content_response(updated, version)


class ApproveContent:
    def __init__(self, repo: SqliteAdminCmsRepository) -> None:
        self.repo = repo

    def execute(self, *, content_id: str, actor_role: str, actor_id: str, comments: str | None) -> CmsContentResponse:
        role = _ensure_role(actor_role)
        item = self.repo.get_item(content_id=content_id)
        if item is None:
            raise ValueError("Khong tim thay content.")
        if not can_approve(role=role, item=item):
            raise ValueError("Role hien tai khong duoc approve content nay.")
        updated = replace(item, workflow_state="approved", updated_by=actor_id, updated_at=utc_now_iso())
        self.repo.save_item(updated)
        self.repo.complete_review_task(content_id=content_id, reviewer_id=actor_id, comments=comments)
        version = self.repo.get_version(content_id=content_id, version_number=updated.current_version)
        if version is None:
            raise ValueError("Khong tim thay version de approve.")
        reviewed_version = replace(
            version,
            status="approved",
            reviewed_by=actor_id if role in {"reviewer", "moderator", "admin"} else version.reviewed_by,
            compliance_reviewed_by=actor_id if role in {"compliance_reviewer", "admin"} else version.compliance_reviewed_by,
        )
        self.repo.save_version(reviewed_version)
        return _to_content_response(updated, reviewed_version)


class PublishContent:
    def __init__(self, repo: SqliteAdminCmsRepository) -> None:
        self.repo = repo

    def execute(self, *, content_id: str, actor_role: str, actor_id: str, comments: str | None) -> CmsContentResponse:
        role = _ensure_role(actor_role)
        if not can_publish(role=role):
            raise ValueError("Chi admin moi duoc publish.")
        item = self.repo.get_item(content_id=content_id)
        if item is None:
            raise ValueError("Khong tim thay content.")
        if item.workflow_state != "approved":
            raise ValueError("Chi content da approved moi duoc publish.")
        version = self.repo.get_version(content_id=content_id, version_number=item.current_version)
        if version is None:
            raise ValueError("Khong tim thay version de publish.")
        updated_item = replace(
            item,
            workflow_state="published",
            published_version=item.current_version,
            updated_by=actor_id,
            updated_at=utc_now_iso(),
        )
        published_version = replace(
            version,
            status="published",
            published_by=actor_id,
            published_at=utc_now_iso(),
        )
        self.repo.save_item(updated_item)
        self.repo.save_version(published_version)
        self.repo.save_publish_event(
            CmsPublishEvent(
                event_id=new_publish_event_id(),
                content_id=content_id,
                version_number=published_version.version_number,
                action="publish",
                actor_role=role,
                actor_id=actor_id,
                notes=comments,
            )
        )
        return _to_content_response(updated_item, published_version)


class ArchiveContent:
    def __init__(self, repo: SqliteAdminCmsRepository) -> None:
        self.repo = repo

    def execute(self, *, content_id: str, actor_role: str, actor_id: str, comments: str | None) -> CmsContentResponse:
        role = _ensure_role(actor_role)
        if not can_archive(role=role):
            raise ValueError("Chi admin moi duoc archive.")
        item = self.repo.get_item(content_id=content_id)
        if item is None:
            raise ValueError("Khong tim thay content.")
        updated = replace(item, workflow_state="archived", updated_by=actor_id, updated_at=utc_now_iso())
        self.repo.save_item(updated)
        version = self.repo.get_version(content_id=content_id, version_number=item.current_version)
        self.repo.save_publish_event(
            CmsPublishEvent(
                event_id=new_publish_event_id(),
                content_id=content_id,
                version_number=item.current_version,
                action="archive",
                actor_role=role,
                actor_id=actor_id,
                notes=comments,
            )
        )
        return _to_content_response(updated, version)


class RollbackContent:
    def __init__(self, repo: SqliteAdminCmsRepository) -> None:
        self.repo = repo

    def execute(self, *, content_id: str, version_number: int, actor_role: str, actor_id: str, comments: str | None) -> CmsContentResponse:
        role = _ensure_role(actor_role)
        if not can_publish(role=role):
            raise ValueError("Chi admin moi duoc rollback.")
        item = self.repo.get_item(content_id=content_id)
        source = self.repo.get_version(content_id=content_id, version_number=version_number)
        if item is None or source is None:
            raise ValueError("Khong tim thay content/version de rollback.")
        now = utc_now_iso()
        next_version = CmsContentVersion(
            version_id=new_version_id(),
            content_id=content_id,
            version_number=item.current_version + 1,
            payload=source.payload,
            status="published",
            origin=source.origin,
            change_summary=f"Rollback from version {version_number}",
            created_by=actor_id,
            reviewed_by=source.reviewed_by,
            compliance_reviewed_by=source.compliance_reviewed_by,
            published_by=actor_id,
            created_at=now,
            published_at=now,
        )
        updated_item = replace(
            item,
            workflow_state="published",
            current_version=next_version.version_number,
            published_version=next_version.version_number,
            updated_by=actor_id,
            updated_at=now,
        )
        self.repo.save_item(updated_item)
        self.repo.save_version(next_version)
        self.repo.save_publish_event(
            CmsPublishEvent(
                event_id=new_publish_event_id(),
                content_id=content_id,
                version_number=next_version.version_number,
                action="rollback",
                actor_role=role,
                actor_id=actor_id,
                notes=comments,
            )
        )
        return _to_content_response(updated_item, next_version)


class ListContent:
    def __init__(self, repo: SqliteAdminCmsRepository) -> None:
        self.repo = repo

    def execute(self, *, content_type: str | None = None) -> list[CmsContentResponse]:
        items = self.repo.list_items(content_type=content_type)
        responses: list[CmsContentResponse] = []
        for item in items:
            version = self.repo.get_version(content_id=item.content_id, version_number=item.current_version)
            responses.append(_to_content_response(item, version))
        return responses


class GetContentDetail:
    def __init__(self, repo: SqliteAdminCmsRepository) -> None:
        self.repo = repo

    def execute(self, *, content_id: str) -> CmsContentResponse:
        item = self.repo.get_item(content_id=content_id)
        if item is None:
            raise ValueError("Khong tim thay content.")
        version = self.repo.get_version(content_id=content_id, version_number=item.current_version)
        return _to_content_response(item, version)


class ListContentVersions:
    def __init__(self, repo: SqliteAdminCmsRepository) -> None:
        self.repo = repo

    def execute(self, *, content_id: str) -> list[CmsContentVersionResponse]:
        versions = self.repo.list_versions(content_id=content_id)
        return [_to_version_response(item) for item in versions]


class ListReviewQueue:
    def __init__(self, repo: SqliteAdminCmsRepository) -> None:
        self.repo = repo

    def execute(self) -> list[CmsReviewTaskResponse]:
        return [_to_review_task_response(item) for item in self.repo.list_review_tasks(status="pending")]


class GetAnalyticsOverview:
    def __init__(self, repo: SqliteAdminCmsRepository) -> None:
        self.repo = repo

    def execute(self) -> dict[str, object]:
        return self.repo.analytics_overview()


class GetContentAnalytics:
    def __init__(self, repo: SqliteAdminCmsRepository) -> None:
        self.repo = repo

    def execute(self, *, content_id: str) -> CmsAnalyticsResponse:
        return CmsAnalyticsResponse(**self.repo.get_analytics(content_id=content_id))


class RecordContentAnalytics:
    def __init__(self, repo: SqliteAdminCmsRepository) -> None:
        self.repo = repo

    def execute(self, *, content_id: str, event_type: str) -> CmsAnalyticsResponse:
        return CmsAnalyticsResponse(**self.repo.upsert_analytics(content_id=content_id, event_type=event_type, occurred_at=utc_now_iso()))


class GenerateAiDraft:
    def __init__(self, repo: SqliteAdminCmsRepository) -> None:
        self.repo = repo
        self.upsert = UpsertContentDraft(repo=repo)
        self.trust = TrustSafetyService()

    def execute(
        self,
        *,
        content_type: str,
        title: str,
        prompt: str,
        locale: str,
        owner_team: str,
        risk_category: str,
        actor_role: str,
        actor_id: str,
    ) -> CmsContentResponse:
        role = _ensure_role(actor_role)
        if role not in {"admin", "editor"}:
            raise ValueError("Chi admin/editor moi duoc tao AI draft.")
        payload = _build_ai_payload(content_type=content_type, title=title, prompt=prompt)
        response = self.upsert.execute(
            content_type=content_type,
            content_id=None,
            slug=_slugify(title),
            title=title,
            locale=locale,
            owner_team=owner_team,
            risk_category=risk_category,
            payload=payload,
            change_summary=f"AI-assisted draft: {prompt[:120]}",
            actor_role=role,
            actor_id=actor_id,
            origin="ai_assisted",
        )
        self.trust.record_audit(
            actor_id=actor_id,
            surface="admin_cms",
            topic=content_type,
            channel="cms_ai_draft",
            risk_classes=(),
            route_decision="draft_only_guardrail",
            input_summary=prompt,
            output_summary=title,
            escalation_action="human_review_required",
        )
        return response


def _to_content_response(item: CmsContentItem, version: CmsContentVersion | None) -> CmsContentResponse:
    return CmsContentResponse(
        content_id=item.content_id,
        content_type=item.content_type,
        slug=item.slug,
        title=item.title,
        locale=item.locale,
        owner_team=item.owner_team,
        risk_category=item.risk_category,
        workflow_state=item.workflow_state,
        current_version=item.current_version,
        published_version=item.published_version,
        created_by=item.created_by,
        updated_by=item.updated_by,
        created_at=item.created_at,
        updated_at=item.updated_at,
        latest_payload=version.payload if version else {},
        latest_origin=version.origin if version else "human",
    )


def _to_version_response(version: CmsContentVersion) -> CmsContentVersionResponse:
    return CmsContentVersionResponse(
        version_id=version.version_id,
        version_number=version.version_number,
        status=version.status,
        origin=version.origin,
        change_summary=version.change_summary,
        created_by=version.created_by,
        reviewed_by=version.reviewed_by,
        compliance_reviewed_by=version.compliance_reviewed_by,
        published_by=version.published_by,
        created_at=version.created_at,
        published_at=version.published_at,
        payload=version.payload,
    )


def _to_review_task_response(task: CmsReviewTask) -> CmsReviewTaskResponse:
    return CmsReviewTaskResponse(
        task_id=task.task_id,
        content_id=task.content_id,
        version_number=task.version_number,
        review_type=task.review_type,
        assignee_role=task.assignee_role,
        status=task.status,
        created_by=task.created_by,
        reviewer_id=task.reviewer_id,
        comments=task.comments,
        created_at=task.created_at,
        completed_at=task.completed_at,
    )


def _slugify(text: str) -> str:
    return "-".join(part for part in text.lower().replace("/", " ").replace("_", " ").split() if part)


def _build_ai_payload(*, content_type: str, title: str, prompt: str) -> dict[str, object]:
    common_body = [
        f"Muc tieu: {title}",
        f"AI draft summary: {prompt}",
        "Can human review truoc khi dua ra public.",
    ]
    if content_type == "glossary_term":
        return {
            "term": title,
            "short_definition": prompt[:180],
            "long_definition": " / ".join(common_body),
            "aliases": [],
        }
    if content_type == "path":
        return {
            "path_id": _slugify(title),
            "title": title,
            "persona_segment": "starter",
            "lesson_ids": [],
            "description": " ".join(common_body),
        }
    if content_type == "nudge_template":
        return {
            "title_template": title,
            "message_template": f"{prompt}. Bat dau bang mot buoc nho va ro rang.",
            "cta_label": "Mo tiep",
            "cta_path_template": "/learn",
        }
    if content_type == "disclaimer_block":
        return {
            "short_text": f"{title}: {prompt[:120]}",
            "full_text": " ".join(common_body),
            "severity": "medium",
        }
    if content_type == "community_policy_snippet":
        return {
            "policy_type": "community_safety",
            "title": title,
            "body": " ".join(common_body),
            "risk_tags": ["trust_first"],
        }
    return {
        "title": title,
        "body": common_body,
        "notes": "AI-assisted draft only",
    }
