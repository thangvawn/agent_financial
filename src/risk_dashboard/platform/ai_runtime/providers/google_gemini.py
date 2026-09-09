from __future__ import annotations

import asyncio
import os
import time
from collections.abc import AsyncIterator
from typing import Any

from risk_dashboard.platform.ai_runtime.contracts import ModelError, ModelResult, ModelTask, StreamEvent, TokenUsage

from risk_dashboard.platform.ai_runtime.redaction import redact_for_provider
from risk_dashboard.platform.ai_runtime.structured import parse_structured
from risk_dashboard.platform.ai_runtime.telemetry import calculate_cost_usd

MODEL_NAME = "gemini-3.5-flash"


def create_gemini_provider(api_key: str | None = None) -> GeminiAdapter:
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ModelError("configuration_error", "GEMINI_API_KEY is not configured on the server.")
    return GeminiAdapter(api_key=key)


def _fc_dict(fc: Any) -> dict[str, Any]:
    raw = getattr(fc, "args", None)
    args = dict(raw) if isinstance(raw, dict) else (dict(raw) if raw is not None else {})
    return {"name": getattr(fc, "name", ""), "args": args}


def _extract_tool_calls(response: Any) -> tuple[dict[str, Any], ...]:
    calls = [_fc_dict(fc) for fc in getattr(response, "function_calls", None) or []]
    if not calls and getattr(response, "candidates", None):
        parts = getattr(getattr(response.candidates[0], "content", None), "parts", []) or []
        calls = [_fc_dict(p.function_call) for p in parts if getattr(p, "function_call", None)]
    return tuple(calls)



class GeminiAdapter:
    name = "gemini"
    default_model = MODEL_NAME

    def __init__(self, *, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ModelError("configuration_error", "GEMINI_API_KEY is required.")

    def _client(self):
        try:
            from google import genai
        except ImportError as exc:
            raise ModelError("configuration_error", "google-genai is not installed.") from exc
        return genai.Client(api_key=self.api_key)

    @staticmethod
    def _request(task: ModelTask) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        sys_parts = [m.content for m in task.messages if m.role == "system"]
        contents = [
            {"role": "model" if m.role == "assistant" else "user", "parts": [{"text": m.content}]}
            for m in task.messages if m.role != "system"
        ] or [{"role": "user", "parts": [{"text": "Execute task"}]}]
        config: dict[str, Any] = {
            "temperature": task.settings.temperature,
            "max_output_tokens": task.settings.max_output_tokens,
        }
        if sys_parts:
            config["system_instruction"] = "\n\n".join(sys_parts)
        if task.settings.response_format == "json_object":
            config["response_mime_type"] = "application/json"
        if task.tool_schemas:
            config["tools"] = list(task.tool_schemas)
        return contents, config

    @staticmethod
    def _usage(response: Any) -> TokenUsage:
        meta = getattr(response, "usage_metadata", None)
        p = int(getattr(meta, "prompt_token_count", 0) or 0)
        c = int(getattr(meta, "candidates_token_count", 0) or 0)
        return TokenUsage(prompt=p, completion=c, total=int(getattr(meta, "total_token_count", p + c) or 0))

    @staticmethod
    def _provider_error(exc: Exception) -> ModelError:
        s = getattr(exc, "code", None)
        if s in {401, 403}:
            return ModelError("provider_auth_error", "Gemini authentication failed.")
        return ModelError("rate_limited" if s == 429 else "provider_unavailable", "Gemini request failed.", retryable=True)

    async def generate(self, task: ModelTask) -> ModelResult:
        started = time.monotonic()
        contents, config = self._request(redact_for_provider(task))
        try:
            response = await asyncio.wait_for(
                self._client().aio.models.generate_content(
                    model=MODEL_NAME, contents=contents, config=config,
                ),
                timeout=task.deadline_seconds,
            )
        except asyncio.TimeoutError as exc:
            raise ModelError("deadline_exceeded", "Gemini request exceeded deadline.") from exc
        except asyncio.CancelledError as exc:
            raise ModelError("cancelled", "Gemini request was cancelled.") from exc
        except ModelError:
            raise
        except Exception as exc:
            raise self._provider_error(exc) from exc

        cand = (getattr(response, "candidates", None) or [None])[0]
        fr = getattr(cand, "finish_reason", "STOP") if cand else "STOP"
        fr_str = (fr if isinstance(fr, str) else (fr.name if hasattr(fr, "name") and isinstance(fr.name, str) else "STOP")).upper()
        pb = getattr(getattr(response, "prompt_feedback", None), "block_reason", None)
        pb_str = (pb if isinstance(pb, str) else (pb.name if hasattr(pb, "name") and isinstance(pb.name, str) else "")).upper()
        if fr_str in {"SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII", "MALICIOUS"} or pb_str in {"SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII", "MALICIOUS"}:
            raise ModelError("safety_blocked", "Gemini generation blocked by safety filters.")


        usage = self._usage(response)
        cost = calculate_cost_usd(MODEL_NAME, usage.prompt, usage.completion)
        if task.max_cost_usd is not None and cost > task.max_cost_usd:
            raise ModelError("budget_exceeded", f"Gemini cost ${cost:.6f} exceeded max budget ${task.max_cost_usd:.6f}.")

        try:
            text = getattr(response, "text", "") or ""
        except Exception:
            text = ""
        parsed = parse_structured(text, task.output_schema) if task.output_schema and text else None
        return ModelResult(
            parsed=parsed,
            text=text,
            tool_calls=_extract_tool_calls(response),
            usage=usage,
            provider=self.name,
            model=MODEL_NAME,
            latency_ms=round((time.monotonic() - started) * 1000),
            finish_reason=fr_str.lower(),
        )

    async def stream(self, task: ModelTask) -> AsyncIterator[StreamEvent]:
        started = time.monotonic()
        contents, config = self._request(redact_for_provider(task))
        seq = 0
        yield StreamEvent(sequence=seq, event="start", correlation_id=task.correlation_id)
        seq += 1
        accumulated_text: list[str] = []
        usage = TokenUsage()

        stream_iter = None
        try:
            stream_iter = await asyncio.wait_for(
                self._client().aio.models.generate_content_stream(model=MODEL_NAME, contents=contents, config=config),
                timeout=task.deadline_seconds,
            )
            while True:
                remaining = task.deadline_seconds - (time.monotonic() - started)
                if remaining <= 0:
                    raise ModelError("deadline_exceeded", "Gemini stream exceeded deadline.")
                try:
                    chunk = await asyncio.wait_for(anext(stream_iter), timeout=remaining)
                except StopAsyncIteration:
                    break
                except asyncio.TimeoutError as exc:
                    raise ModelError("deadline_exceeded", "Gemini stream exceeded deadline.") from exc
                usage = self._usage(chunk)
                chunk_text = getattr(chunk, "text", "") or ""
                if chunk_text:
                    accumulated_text.append(chunk_text)
                    yield StreamEvent(sequence=seq, event="token", correlation_id=task.correlation_id, delta=chunk_text)
                    seq += 1
        except asyncio.CancelledError as exc:
            raise ModelError("cancelled", "Gemini stream was cancelled.") from exc
        except ModelError:
            raise
        except Exception as exc:
            raise self._provider_error(exc) from exc
        finally:
            close = getattr(stream_iter, "aclose", None)
            if close is not None:
                await close()

        full_text = "".join(accumulated_text)
        parsed = None
        if task.output_schema and full_text:
            try:
                parsed = parse_structured(full_text, task.output_schema)
            except Exception:
                pass
        yield StreamEvent(
            sequence=seq, event="completed", correlation_id=task.correlation_id,
            parsed=parsed, usage=usage, finish_reason="stop",
        )

    async def health(self) -> bool:
        try:
            return bool(self._client())
        except Exception:
            return False
