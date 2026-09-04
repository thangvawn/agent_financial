from __future__ import annotations

import asyncio
import os
import time
from collections.abc import AsyncIterator
from typing import Any

from risk_dashboard.platform.ai_runtime.contracts import (
    ModelError,
    ModelResult,
    ModelTask,
    StreamEvent,
    TokenUsage,
)
from risk_dashboard.platform.ai_runtime.redaction import redact_for_provider
from risk_dashboard.platform.ai_runtime.structured import parse_structured

MODEL_NAME = "gemini-3.5-flash"


def create_gemini_provider(api_key: str | None = None) -> GeminiAdapter:
    """Factory creating a GeminiAdapter using environment or explicit key."""
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ModelError("configuration_error", "GEMINI_API_KEY is not configured on the server.")
    return GeminiAdapter(api_key=key)


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
        system_parts = [m.content for m in task.messages if m.role == "system"]
        system_instruction = "\n\n".join(system_parts) if system_parts else None

        contents: list[dict[str, Any]] = []
        for m in task.messages:
            if m.role == "system":
                continue
            gemini_role = "model" if m.role == "assistant" else "user"
            contents.append({"role": gemini_role, "parts": [{"text": m.content}]})

        if not contents:
            contents = [{"role": "user", "parts": [{"text": "Execute task"}]}]

        config: dict[str, Any] = {
            "temperature": task.settings.temperature,
            "max_output_tokens": task.settings.max_output_tokens,
        }
        if system_instruction:
            config["system_instruction"] = system_instruction
        if task.settings.response_format == "json_object":
            config["response_mime_type"] = "application/json"
        return contents, config

    @staticmethod
    def _usage(response: Any) -> TokenUsage:
        metadata = getattr(response, "usage_metadata", None)
        prompt = int(getattr(metadata, "prompt_token_count", 0) or 0)
        completion = int(getattr(metadata, "candidates_token_count", 0) or 0)
        total = int(getattr(metadata, "total_token_count", prompt + completion) or 0)
        return TokenUsage(prompt=prompt, completion=completion, total=total)

    @staticmethod
    def _provider_error(exc: Exception) -> ModelError:
        status = getattr(exc, "code", None)
        if status in {401, 403}:
            return ModelError("provider_auth_error", "Gemini authentication failed.")
        if status == 429:
            return ModelError("rate_limited", "Gemini rate limit exceeded.", retryable=True)
        return ModelError("provider_unavailable", "Gemini request failed.", retryable=True)

    async def generate(self, task: ModelTask) -> ModelResult:
        started = time.monotonic()
        contents, config = self._request(redact_for_provider(task))
        try:
            response = await asyncio.wait_for(
                self._client().aio.models.generate_content(
                    model=MODEL_NAME,
                    contents=contents,
                    config=config,
                ),
                timeout=task.deadline_seconds,
            )
        except asyncio.TimeoutError as exc:
            raise ModelError("deadline_exceeded", "Gemini request exceeded deadline.") from exc
        except ModelError:
            raise
        except Exception as exc:
            raise self._provider_error(exc) from exc
        text = getattr(response, "text", "") or ""
        parsed = parse_structured(text, task.output_schema) if task.output_schema else None
        return ModelResult(
            parsed=parsed,
            text=text,
            usage=self._usage(response),
            provider=self.name,
            model=MODEL_NAME,
            latency_ms=round((time.monotonic() - started) * 1000),
            finish_reason="stop",
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
                self._client().aio.models.generate_content_stream(
                    model=MODEL_NAME,
                    contents=contents,
                    config=config,
                ),
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
                    yield StreamEvent(
                        sequence=seq,
                        event="token",
                        correlation_id=task.correlation_id,
                        delta=chunk_text,
                    )
                    seq += 1
        except (ModelError, asyncio.CancelledError):
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
            sequence=seq,
            event="completed",
            correlation_id=task.correlation_id,
            parsed=parsed,
            usage=usage,
            finish_reason="stop",
        )

    async def health(self) -> bool:
        try:
            self._client()
        except Exception:
            return False
        return True
