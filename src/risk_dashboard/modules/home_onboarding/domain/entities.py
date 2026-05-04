from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class OnboardingSession:
    session_id: str
    started_at: str = field(default_factory=utc_now_iso)
    last_step: str = "goal"
    answers: dict[str, str] = field(default_factory=dict)
    completed_at: str | None = None


@dataclass
class OnboardingProfile:
    session_id: str
    primary_goal: str
    knowledge_level: str
    risk_tolerance_prelim: str
    primary_interest: str
    current_state: str
    persona_segment: str
    guided_investing_eligible: bool
    pro_eligible: bool
    primary_route: str
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class RouteDecision:
    persona_segment: str
    primary_route: str
    guided_investing_eligible: bool
    pro_eligible: bool
    trust_message: str


@dataclass(frozen=True)
class HomeBlock:
    block_id: str
    title: str
    description: str
    cta_label: str | None = None
    cta_path: str | None = None


@dataclass(frozen=True)
class HomeState:
    session_id: str
    persona_segment: str
    primary_route: str
    next_best_action_type: str
    next_best_action_ref: str
    trust_message: str
    blocks: list[HomeBlock]
