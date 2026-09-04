from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

Surface = Literal["learn", "bctc", "simulation", "news", "market"]


class SummarySourceRefV1(BaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    surface: Surface
    resource_type: str
    resource_id: str
    resource_version: int = Field(ge=1)


class HomeDomainSummaryV1(BaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    summary_id: str
    account_id: str  # internal-only, excluded in public card rendering
    surface: Surface
    kind: Literal[
        "learning_progress",
        "research_artifact",
        "stale_artifact",
        "market_education",
    ]
    title: str = Field(max_length=120)
    compact_summary: str = Field(max_length=500)
    source_ref: SummarySourceRefV1
    review_status: Literal["reviewed", "accepted"]
    review_policy_version: str
    allowed_action_type: str
    allowed_cta_path: str
    state: Literal["incomplete", "open_question", "stale", "ready"]
    created_at: str
    updated_at: str
    expires_at: str


class ExplicitHomeMemoryV1(BaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    memory_id: str
    memory_type: Literal["preference", "goal", "mastery"]
    value: str = Field(max_length=200)
    provenance: Literal[
        "user_stated",
        "user_approved_plan",
        "deterministic_checkpoint",
    ]
    verified: bool
    consent_policy_version: str
    expires_at: str | None = None


class JourneyContextV1(BaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    account_id: str
    principal_scopes: tuple[str, ...] = ()
    consent_policy_version: str = "1.0.0"
    personalization_consented: bool = False
    memory_consented: bool = False
    locale: str = "vi-VN"
    onboarding_state: str = ""
    summaries: tuple[HomeDomainSummaryV1, ...] = ()
    explicit_memories: tuple[ExplicitHomeMemoryV1, ...] = ()
    dismissed_candidate_ids: tuple[str, ...] = ()
    snoozed_until_by_candidate: dict[str, str] = Field(default_factory=dict)
    available_surfaces: tuple[Surface, ...] = ()
    built_at: str


class NextBestActionCardV1(BaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    card_id: str
    candidate_id: str
    action_type: str
    target_surface: Surface
    target_ref: SummarySourceRefV1
    title: str = Field(max_length=120)
    why_now: str = Field(max_length=300)
    source_summary_ids: tuple[str, ...] = ()
    estimated_minutes: int | None = Field(default=None, ge=1, le=180)
    limitations: tuple[str, ...] = ()
    cta_label: str = Field(max_length=80)
    cta_path: str
    created_at: str
    expires_at: str
    dismissible: bool = True
    snooze_options_hours: tuple[int, ...] = (24, 72, 168)


class HomeJourneyResponseV1(BaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    generated_at: str
    mode: Literal["personalized", "non_personalized", "empty"]
    next_best_action: NextBestActionCardV1 | None = None
    stale_sources_omitted: int = 0
    consent_required: bool = False


class HomeJourneyFeedbackRequestV1(BaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    action: Literal["dismiss", "snooze", "complete"]
    snooze_hours: Literal[24, 72, 168] | None = None
    idempotency_key: str = Field(min_length=8, max_length=128)


class HomeJourneyFeedbackReceiptV1(BaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    receipt_id: str
    card_id: str
    status: Literal["recorded", "duplicate", "expired", "not_found"]
    recorded_at: str

