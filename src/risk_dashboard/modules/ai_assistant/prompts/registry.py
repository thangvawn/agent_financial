from __future__ import annotations

from dataclasses import dataclass


PROMPT_REGISTRY_VERSION = "assistant_prompt_registry_v2"


@dataclass(frozen=True)
class AssistantPromptPolicy:
    role: str
    version: str
    system_rule: str
    output_rule: str


PROMPT_POLICIES: dict[str, AssistantPromptPolicy] = {
    "tutor": AssistantPromptPolicy(
        role="tutor",
        version=PROMPT_REGISTRY_VERSION,
        system_rule="Explain one concept at a time using plain language and a short check-understanding question.",
        output_rule="Return summary, explanation, check question, and one next lesson hint.",
    ),
    "coach": AssistantPromptPolicy(
        role="coach",
        version=PROMPT_REGISTRY_VERSION,
        system_rule="Prioritize one small safe action grounded in available user state.",
        output_rule="Return why this step matters, one next action, and avoid pressure or urgency.",
    ),
    "analyst": AssistantPromptPolicy(
        role="analyst",
        version=PROMPT_REGISTRY_VERSION,
        system_rule="Explain market/company/risk context without picks, certainty, or personalized advice.",
        output_rule="Return what changed, why it matters, what not to overread, freshness, and next safe path.",
    ),
    "pro_assistant": AssistantPromptPolicy(
        role="pro_assistant",
        version=PROMPT_REGISTRY_VERSION,
        system_rule="Support research workflow with assumptions, caveats, and next research questions.",
        output_rule="Return objective, assumptions, caveats, findings, and next research step.",
    ),
}


def get_prompt_policy(role: str) -> AssistantPromptPolicy:
    return PROMPT_POLICIES.get(role, PROMPT_POLICIES["tutor"])
