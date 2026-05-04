from __future__ import annotations

from dataclasses import replace
import json
import os
import re
from typing import Any

from risk_dashboard.modules.ai_assistant.domain.entities import AssistantMessage, AssistantReply
from risk_dashboard.modules.ai_assistant.prompts.registry import AssistantPromptPolicy


class AIAgentRuntime:
    """Optional model-backed composition layer.

    The deterministic router/tool/safety pipeline still owns decisions. The model
    only turns a safe draft plus bounded context into a more conversational answer.
    If model access is unavailable or malformed, callers keep the deterministic draft.
    """

    def __init__(self) -> None:
        self.enabled = os.getenv("AI_ASSISTANT_AGENT_ENABLED", "1").strip().lower() not in {"0", "false", "no"}
        self.model_name = os.getenv("AI_ASSISTANT_MODEL", os.getenv("TRADING_LAB_MODEL", "gpt-4o-mini"))

    def compose(
        self,
        *,
        draft: AssistantReply,
        user_prompt: str,
        surface: str,
        context: dict[str, object],
        history: tuple[AssistantMessage, ...],
        prompt_policy: AssistantPromptPolicy,
        guardrails: tuple[str, ...],
    ) -> AssistantReply:
        if not self.enabled or not os.getenv("OPENAI_API_KEY") or not draft.allowed:
            return draft
        try:
            payload = self._invoke_model(
                draft=draft,
                user_prompt=user_prompt,
                surface=surface,
                context=context,
                history=history,
                prompt_policy=prompt_policy,
                guardrails=guardrails,
            )
        except Exception:
            return draft

        return self._merge_agent_payload(draft=draft, payload=payload)

    def _invoke_model(
        self,
        *,
        draft: AssistantReply,
        user_prompt: str,
        surface: str,
        context: dict[str, object],
        history: tuple[AssistantMessage, ...],
        prompt_policy: AssistantPromptPolicy,
        guardrails: tuple[str, ...],
    ) -> dict[str, Any]:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model=self.model_name, temperature=0.25, timeout=8, max_retries=0)
        response = llm.invoke(
            [
                SystemMessage(content=_system_prompt(prompt_policy=prompt_policy)),
                HumanMessage(
                    content=json.dumps(
                        {
                            "surface": surface,
                            "role": draft.role,
                            "user_prompt": user_prompt,
                            "recent_history": _history_payload(history),
                            "compact_context": _compact_context(context),
                            "safe_draft": {
                                "title": draft.title,
                                "summary": draft.summary,
                                "explanation": draft.explanation,
                                "next_step": draft.next_step,
                                "cta_path": draft.cta_path,
                                "confidence_note": draft.confidence_note,
                                "check_question": draft.check_question,
                            },
                            "guardrails": list(guardrails),
                        },
                        ensure_ascii=False,
                    )
                ),
            ]
        )
        return _parse_json_object(str(response.content))

    def _merge_agent_payload(self, *, draft: AssistantReply, payload: dict[str, Any]) -> AssistantReply:
        title = _clean_text(payload.get("title"), fallback=draft.title, limit=120)
        summary = _clean_text(payload.get("summary"), fallback=draft.summary, limit=260)
        explanation = _clean_text(payload.get("explanation"), fallback=draft.explanation, limit=1400)
        next_step = _clean_text(payload.get("next_step"), fallback=draft.next_step, limit=220)
        check_question = payload.get("check_question")
        if check_question is not None:
            check_question = _clean_text(check_question, fallback=draft.check_question or "", limit=180) or None

        confidence_note = draft.confidence_note
        agent_note = _clean_text(payload.get("confidence_note"), fallback="", limit=220)
        if agent_note and agent_note not in confidence_note:
            confidence_note = f"{confidence_note} Agent note: {agent_note}"

        return replace(
            draft,
            title=title,
            summary=summary,
            explanation=explanation,
            next_step=next_step,
            check_question=check_question,
            confidence_note=confidence_note,
        )


def _system_prompt(*, prompt_policy: AssistantPromptPolicy) -> str:
    return "\n".join(
        [
            "You are the production AI assistant for a public fintech education product.",
            "You are an agentic response composer, not a classifier and not an investment advisor.",
            "Use the safe_draft as the source of truth for allowed scope, CTA, and risk posture.",
            "Use recent_history to respond naturally to follow-up questions and avoid repeating yourself.",
            "Use compact_context only when it is present. Never invent missing user data, market data, prices, or performance.",
            "Keep the answer concise, useful, and conversational in Vietnamese unless the user wrote in English.",
            "Do not recommend buying/selling securities, do not imply certainty, and do not override guardrails.",
            f"Role rule: {prompt_policy.system_rule}",
            f"Output rule: {prompt_policy.output_rule}",
            "Return strict JSON only with keys: title, summary, explanation, next_step, check_question, confidence_note.",
        ]
    )


def _history_payload(history: tuple[AssistantMessage, ...]) -> list[dict[str, str]]:
    payload: list[dict[str, str]] = []
    for message in history[-8:]:
        content = re.sub(r"\s+", " ", message.content or "").strip()
        if not content:
            continue
        payload.append({"sender": message.sender, "content": content[:600]})
    return payload


def _compact_context(context: dict[str, object]) -> dict[str, object]:
    allowed_keys = {
        "knowledge_level",
        "persona_segment",
        "home",
        "learning",
        "goal",
        "financial_health",
        "guided_investing",
        "watchlist",
    }
    compact: dict[str, object] = {}
    for key, value in context.items():
        if key not in allowed_keys:
            continue
        compact[key] = value
    return compact


def _parse_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end >= start:
        cleaned = cleaned[start : end + 1]
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise ValueError("Agent response must be a JSON object.")
    return payload


def _clean_text(value: object, *, fallback: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not text:
        return fallback
    return text[:limit].rstrip()
