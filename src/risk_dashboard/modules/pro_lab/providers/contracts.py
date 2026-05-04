from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProLabCommandDefinition:
    command_id: str
    label: str
    description: str
    input_schema: dict[str, object]
    output_schema: dict[str, object]
    risk_level: str = "medium"
    async_supported: bool = False
    requires_review: bool = True
    public_allowed: bool = False
    private_only: bool = False


@dataclass(frozen=True)
class ProLabProviderDefinition:
    provider_id: str
    label: str
    category: str
    description: str
    enabled: bool
    commands: tuple[ProLabCommandDefinition, ...]
    guardrails: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ProLabProviderResult:
    status: str
    output_payload: dict[str, object]
    logs: tuple[dict[str, object], ...]
    progress_pct: int
    safety_flags: tuple[str, ...]
    data_freshness: dict[str, object]
