from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class IntentDecision:
    intent: str
    confidence: float
    reason: str
    risk_labels: tuple[str, ...] = ()
    needs_clarification: bool = False


@dataclass(frozen=True)
class ModeDecision:
    role: str
    confidence: float
    reason: str
    allowed_tools: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContextSignal:
    key: str
    value: object
    source: str
    freshness: str = "unknown"


@dataclass(frozen=True)
class AssistantContextPack:
    user_id: str
    surface: str
    knowledge_level: str
    persona_segment: str | None
    signals: tuple[ContextSignal, ...]
    compact_context: dict[str, object]
    missing_context: tuple[str, ...] = ()
    freshness: str = "fresh"


@dataclass(frozen=True)
class SafetyDecision:
    action: str
    risk_labels: tuple[str, ...]
    warnings: tuple[str, ...]
    fallback_title: str | None = None
    fallback_summary: str | None = None
    fallback_next_step: str | None = None


@dataclass(frozen=True)
class AssistantAction:
    label: str
    path: str
    kind: str = "open_module"


@dataclass(frozen=True)
class AssistantSource:
    label: str
    source_type: str
    freshness: str = "unknown"


@dataclass(frozen=True)
class StructuredAssistantPayload:
    mode_used: str
    intent: str
    intent_confidence: float
    confidence_label: str
    data_freshness: str
    warnings: tuple[str, ...] = ()
    next_actions: tuple[AssistantAction, ...] = ()
    suggested_modules: tuple[str, ...] = ()
    learning_suggestions: tuple[str, ...] = ()
    sources: tuple[AssistantSource, ...] = ()
    response_blocks: tuple[dict[str, object], ...] = field(default_factory=tuple)
