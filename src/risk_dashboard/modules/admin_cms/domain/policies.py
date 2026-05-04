from __future__ import annotations

from risk_dashboard.modules.admin_cms.domain.entities import CmsContentItem

VALID_WORKFLOW_STATES = {"draft", "review", "approved", "published", "archived"}
VALID_CONTENT_TYPES = {
    "course",
    "path",
    "lesson",
    "quiz",
    "glossary_term",
    "contextual_explainer",
    "nudge_template",
    "disclaimer_block",
    "community_policy_snippet",
}
VALID_ROLES = {"admin", "editor", "reviewer", "compliance_reviewer", "moderator"}
COMPLIANCE_REQUIRED_TYPES = {"disclaimer_block", "community_policy_snippet"}
COMPLIANCE_REQUIRED_RISK = {"investing", "scenario", "policy", "legal", "compliance"}


def requires_compliance(*, content_type: str, risk_category: str) -> bool:
    return content_type in COMPLIANCE_REQUIRED_TYPES or risk_category in COMPLIANCE_REQUIRED_RISK


def can_edit(*, role: str, content_type: str) -> bool:
    if role == "admin":
        return True
    if role == "editor":
        return True
    if role == "moderator" and content_type == "community_policy_snippet":
        return True
    return False


def can_submit_review(*, role: str, content_type: str) -> bool:
    return can_edit(role=role, content_type=content_type) or role == "admin"


def can_approve(*, role: str, item: CmsContentItem) -> bool:
    if role == "admin":
        return True
    if requires_compliance(content_type=item.content_type, risk_category=item.risk_category):
        return role == "compliance_reviewer"
    if item.content_type == "community_policy_snippet":
        return role in {"reviewer", "moderator"}
    return role == "reviewer"


def can_publish(*, role: str) -> bool:
    return role == "admin"


def can_archive(*, role: str) -> bool:
    return role == "admin"


def next_review_type(*, content_type: str, risk_category: str) -> str:
    return "compliance" if requires_compliance(content_type=content_type, risk_category=risk_category) else "editorial"


def role_permissions(role: str) -> list[str]:
    mapping = {
        "admin": ["edit", "submit_review", "approve", "publish", "archive", "rollback", "ai_generate"],
        "editor": ["edit", "submit_review", "ai_generate"],
        "reviewer": ["approve_safe_content"],
        "compliance_reviewer": ["approve_compliance_required_content"],
        "moderator": ["edit_community_policy", "submit_review_community_policy", "approve_community_policy"],
    }
    return mapping.get(role, [])
