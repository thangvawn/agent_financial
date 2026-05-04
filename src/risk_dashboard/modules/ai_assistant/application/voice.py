from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class VoiceSynthesisResult:
    provider: str
    enabled: bool
    mime_type: str
    audio_base64: str | None
    fallback_reason: str | None
    voice_id: str | None
    model_id: str | None


class ElevenLabsVoiceRuntime:
    """Server-side ElevenLabs TTS wrapper.

    Keep API key on backend only. Frontend receives either audio payload or
    an explicit fallback reason so it can degrade to browser speech.
    """

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        default_voice_id: str,
        default_model_id: str,
        timeout_seconds: float = 8.0,
    ) -> None:
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.default_voice_id = default_voice_id
        self.default_model_id = default_model_id
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls) -> ElevenLabsVoiceRuntime:
        return cls(
            api_key=os.getenv("ELEVENLABS_API_KEY", ""),
            base_url=os.getenv("ELEVENLABS_BASE_URL", "https://api.elevenlabs.io"),
            default_voice_id=os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL"),
            default_model_id=os.getenv("ELEVENLABS_MODEL_ID", "eleven_flash_v2_5"),
            timeout_seconds=float(os.getenv("ELEVENLABS_TIMEOUT_SECONDS", "8")),
        )

    def synthesize(
        self,
        *,
        text: str,
        voice_id: str | None = None,
        model_id: str | None = None,
    ) -> VoiceSynthesisResult:
        normalized = _normalize_text(text)
        selected_voice_id = voice_id or self.default_voice_id
        selected_model_id = model_id or self.default_model_id

        if not normalized:
            return self._fallback("No text to synthesize.", selected_voice_id, selected_model_id)
        if not self.api_key:
            return self._fallback("ELEVENLABS_API_KEY chưa được cấu hình.", selected_voice_id, selected_model_id)

        endpoint = f"{self.base_url}/v1/text-to-speech/{selected_voice_id}"
        payload = {
            "text": normalized,
            "model_id": selected_model_id,
            "voice_settings": {
                "stability": 0.35,
                "similarity_boost": 0.8,
                "style": 0.15,
                "use_speaker_boost": True,
            },
        }
        request = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key,
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:  # nosec B310
                audio_bytes = response.read()
        except HTTPError as exc:
            detail = _read_error_body(exc)
            return self._fallback(
                f"ElevenLabs HTTP {exc.code}{': ' + detail if detail else ''}",
                selected_voice_id,
                selected_model_id,
            )
        except URLError as exc:
            return self._fallback(f"ElevenLabs network error: {exc.reason}", selected_voice_id, selected_model_id)
        except Exception as exc:  # pragma: no cover - defensive fallback
            return self._fallback(f"ElevenLabs error: {exc}", selected_voice_id, selected_model_id)

        if not audio_bytes:
            return self._fallback("ElevenLabs trả về audio rỗng.", selected_voice_id, selected_model_id)

        return VoiceSynthesisResult(
            provider="elevenlabs",
            enabled=True,
            mime_type="audio/mpeg",
            audio_base64=base64.b64encode(audio_bytes).decode("ascii"),
            fallback_reason=None,
            voice_id=selected_voice_id,
            model_id=selected_model_id,
        )

    def _fallback(self, reason: str, voice_id: str | None, model_id: str | None) -> VoiceSynthesisResult:
        return VoiceSynthesisResult(
            provider="elevenlabs",
            enabled=False,
            mime_type="audio/mpeg",
            audio_base64=None,
            fallback_reason=reason,
            voice_id=voice_id,
            model_id=model_id,
        )


def _normalize_text(text: str) -> str:
    cleaned = " ".join((text or "").strip().split())
    if not cleaned:
        return ""
    return cleaned[:1200]


def _read_error_body(exc: HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8", errors="ignore").strip()
    except Exception:
        return ""
    if not body:
        return ""
    if len(body) > 180:
        return f"{body[:177]}..."
    return body
