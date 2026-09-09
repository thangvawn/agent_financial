from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from risk_dashboard.platform.ai_runtime.contracts import (
    ModelError,
    ModelMessage,
    ModelResult,
    ModelTask,
)
from risk_dashboard.platform.ai_runtime.providers.google_gemini import (
    GeminiAdapter,
    _extract_tool_calls,
)
from risk_dashboard.platform.ai_runtime.redaction import redact_text
from risk_dashboard.platform.ai_runtime.retry import (
    CIRCUIT_BREAKER_RECOVERY_SECONDS,
    _get_breaker,
    _record_failure,
    reset_circuit_breaker,
    with_retry,
)
from risk_dashboard.platform.ai_runtime.structured import parse_structured
from risk_dashboard.platform.ai_runtime.testing.fake_provider import FakeProvider
from risk_dashboard.modules.news_intelligence.application.translation import NewsTranslator


def _task(text: str = "test", **kwargs) -> ModelTask:
    return ModelTask(
        task_type="test",
        system_instructions_ref="test.v1",
        messages=(ModelMessage(role="user", content=text),),
        correlation_id="corr-h",
        **kwargs,
    )


def test_circuit_breaker_recovery_cooldown(monkeypatch: pytest.MonkeyPatch):
    reset_circuit_breaker("fake")
    b = _get_breaker("fake")
    for _ in range(5):
        _record_failure("fake")
    assert b["open"] is True

    provider = FakeProvider(
        scripted=[ModelResult(text="recovered", provider="fake", model="m", latency_ms=1, finish_reason="stop")],
    )
    monkeypatch.setattr(time, "monotonic", lambda: b["last_failure"] + CIRCUIT_BREAKER_RECOVERY_SECONDS + 1.0)
    res = asyncio.run(with_retry(provider, _task("ping")))
    assert res.text == "recovered"
    assert b["open"] is False and b["failures"] == 0



def test_redaction_formatted_pii():
    text = "SĐT 0912 345 678, +84 987 654 321, 0912.333.444, CCCD 001 099 012 345."
    redacted = redact_text(text)
    assert "0912" not in redacted
    assert "0987" not in redacted
    assert "001" not in redacted
    assert redacted.count("[REDACTED_PII]") >= 4


def test_gemini_adapter_safe_text_and_tool_calls_none_args():
    mock_fc = MagicMock(name="search_db", args=None)
    mock_fc.name = "search_db"
    assert _extract_tool_calls(MagicMock(function_calls=[mock_fc]))[0]["args"] == {}

    class ToolOnlyResponse:
        candidates = [MagicMock(finish_reason="STOP", content=MagicMock(parts=[MagicMock(function_call=mock_fc)]))]
        usage_metadata = MagicMock(prompt_token_count=1, candidates_token_count=1, total_token_count=2)

        @property
        def text(self):
            raise ValueError("Candidate has no text parts")

    adapter = GeminiAdapter(api_key="mock_key")
    with patch.object(adapter, "_client", return_value=MagicMock(aio=MagicMock(models=MagicMock(generate_content=AsyncMock(return_value=ToolOnlyResponse()))))):
        res = asyncio.run(adapter.generate(_task("run tool")))
        assert res.text == ""
        assert len(res.tool_calls) == 1 and res.tool_calls[0]["name"] == "search_db"


def test_gemini_adapter_prompt_feedback_safety_block():
    resp = MagicMock(candidates=[], prompt_feedback=MagicMock(block_reason="SAFETY"))
    adapter = GeminiAdapter(api_key="mock_key")
    with patch.object(adapter, "_client", return_value=MagicMock(aio=MagicMock(models=MagicMock(generate_content=AsyncMock(return_value=resp))))):
        with pytest.raises(ModelError) as exc:
            asyncio.run(adapter.generate(_task("unsafe")))
        assert exc.value.code == "safety_blocked"


def test_parse_structured_handles_preamble_and_markdown():
    output = 'Dưới đây là kết quả:\n```json\n{"status": "ok", "value": 100}\n```\nChúc bạn thành công!'
    res = parse_structured(output, {"type": "object", "required": ["status"]})
    assert res["status"] == "ok" and res["value"] == 100


def test_news_translator_handles_markdown_fence():
    mock_prov = MagicMock()
    mock_prov.generate = AsyncMock(return_value=ModelResult(
        text='```json\n{"headline_vi": "Tiêu đề tin", "summary_vi": "Tóm tắt tin"}\n```',
        parsed=None, provider="mock", model="m", latency_ms=1, finish_reason="stop",
    ))
    translator = NewsTranslator(provider=mock_prov)
    with patch.object(translator, "_get_cached", return_value=None), patch.object(translator, "_store_cached"):
        res = translator.translate_item({"headline": "Title", "summary": "Sum"})
        assert res["headline_vi"] == "Tiêu đề tin"
