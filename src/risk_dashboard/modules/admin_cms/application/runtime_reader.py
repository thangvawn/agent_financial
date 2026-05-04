from __future__ import annotations

from dataclasses import dataclass

from risk_dashboard.modules.admin_cms.infrastructure.repositories.sqlite import SqliteAdminCmsRepository


@dataclass(frozen=True)
class RuntimeDisclaimer:
    title: str
    short_text: str
    full_text: str
    severity: str


@dataclass(frozen=True)
class RuntimeContextualExplainer:
    explainer_id: str
    title: str
    body: list[str]
    linked_lesson_ids: list[str]
    guardrail_note: str


class ContentOpsRuntimeReader:
    def __init__(self, repo: SqliteAdminCmsRepository | None = None) -> None:
        self.repo = repo or SqliteAdminCmsRepository()

    def get_disclaimer(self, *, surface: str, topic: str | None = None) -> RuntimeDisclaimer | None:
        exact_match: RuntimeDisclaimer | None = None
        fallback_match: RuntimeDisclaimer | None = None
        for item, version in self.repo.list_published_content(content_type="disclaimer_block"):
            payload = version.payload
            payload_surface = str(payload.get("surface") or "").strip()
            if payload_surface and payload_surface != surface:
                continue
            payload_topic = str(payload.get("topic") or item.slug).strip()
            disclaimer = RuntimeDisclaimer(
                title=str(payload.get("title") or item.title),
                short_text=str(payload.get("short_text") or ""),
                full_text=str(payload.get("full_text") or payload.get("short_text") or ""),
                severity=str(payload.get("severity") or "medium"),
            )
            if topic and payload_topic == topic:
                exact_match = disclaimer
                break
            if not payload.get("topic"):
                fallback_match = disclaimer
        return exact_match or fallback_match

    def get_contextual_explainer(
        self,
        *,
        surface: str,
        trigger_key: str | None = None,
        trigger_type: str | None = None,
    ) -> RuntimeContextualExplainer | None:
        exact_match: RuntimeContextualExplainer | None = None
        fallback_match: RuntimeContextualExplainer | None = None
        for item, version in self.repo.list_published_content(content_type="contextual_explainer"):
            payload = version.payload
            payload_surface = str(payload.get("surface") or "").strip()
            if payload_surface and payload_surface != surface:
                continue
            payload_trigger_key = str(payload.get("trigger_key") or item.slug).strip()
            payload_trigger_type = str(payload.get("trigger_type") or "").strip()
            explainer = RuntimeContextualExplainer(
                explainer_id=item.slug,
                title=str(payload.get("title") or item.title),
                body=_coerce_str_list(payload.get("body") or payload.get("body_json")),
                linked_lesson_ids=[str(value) for value in payload.get("linked_lesson_ids", []) if value],
                guardrail_note=str(payload.get("guardrail_note") or ""),
            )
            key_match = trigger_key is not None and payload_trigger_key == trigger_key
            type_match = trigger_type is not None and payload_trigger_type == trigger_type
            if trigger_key is not None and trigger_type is not None and key_match and type_match:
                exact_match = explainer
                break
            if trigger_key is not None and key_match:
                exact_match = explainer
                break
            if trigger_type is not None and type_match:
                exact_match = explainer
                break
            if not payload.get("trigger_key") and not payload.get("trigger_type"):
                fallback_match = explainer
        return exact_match or fallback_match


def _coerce_str_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]
