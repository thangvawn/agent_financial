from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from risk_dashboard.platform.ai_runtime.contracts import (
    ModelError,
    ModelMessage,
    ModelResult,
    ModelTask,
    TokenUsage,
)
from risk_dashboard.platform.ai_runtime.provider import LLMProvider
from risk_dashboard.platform.ai_runtime.providers.google_gemini import GeminiAdapter
from risk_dashboard.platform.ai_runtime.redaction import redact_for_provider, redact_text
from risk_dashboard.platform.ai_runtime.retry import with_retry
from risk_dashboard.platform.ai_runtime.structured import parse_structured
from risk_dashboard.platform.ai_runtime.telemetry import get_usage_summary, reset_usage_summary
from risk_dashboard.platform.ai_runtime.testing.fake_provider import FakeProvider
import risk_dashboard.app.bootstrap.app_factory as app_factory_module
from risk_dashboard.modules.news_intelligence.application.translation import NewsTranslator


def _task(content: str = "Test", **kwargs) -> ModelTask:
    return ModelTask(
        task_type="test",
        system_instructions_ref="test.v1",
        messages=(ModelMessage(role="user", content=content),),
        correlation_id="corr-test",
        **kwargs,
    )


def test_gemini_adapter_tool_schemas_and_parsing():
    async def _test():
        task = _task("Get FPT", tool_schemas=({"name": "quote", "parameters": {"type": "object"}},))
        _, config = GeminiAdapter._request(task)
        assert "tools" in config

        mock_call = MagicMock(args={"ticker": "FPT"})
        mock_call.name = "quote"
        mock_part = MagicMock(function_call=mock_call, text=None)
        mock_cand = MagicMock(finish_reason="STOP", content=MagicMock(parts=[mock_part]))
        resp = MagicMock(text="", candidates=[mock_cand], function_calls=[mock_call], usage_metadata=MagicMock(prompt_token_count=1, candidates_token_count=1, total_token_count=2))
        client = MagicMock()
        client.aio.models.generate_content = AsyncMock(return_value=resp)
        adapter = GeminiAdapter(api_key="key")
        with patch.object(adapter, "_client", return_value=client):
            res = await adapter.generate(task)
        assert len(res.tool_calls) > 0 and res.tool_calls[0]["name"] == "quote"
    asyncio.run(_test())


def test_gemini_raises_safety_blocked():
    async def _test():
        mock_cand = MagicMock(finish_reason="SAFETY")
        resp = MagicMock(text="", candidates=[mock_cand], usage_metadata=MagicMock(prompt_token_count=1, candidates_token_count=0, total_token_count=1))
        client = MagicMock()
        client.aio.models.generate_content = AsyncMock(return_value=resp)
        adapter = GeminiAdapter(api_key="key")
        with patch.object(adapter, "_client", return_value=client):
            with pytest.raises(ModelError) as exc:
                await adapter.generate(_task("unsafe"))
        assert exc.value.code == "safety_blocked"
    asyncio.run(_test())


def test_runtime_enforces_max_cost_budget():
    async def _test():
        task = _task("heavy", max_cost_usd=0.0001)
        resp = MagicMock(text="{}", candidates=[MagicMock(finish_reason="STOP")], usage_metadata=MagicMock(prompt_token_count=100_000, candidates_token_count=50_000, total_token_count=150_000))
        client = MagicMock()
        client.aio.models.generate_content = AsyncMock(return_value=resp)
        adapter = GeminiAdapter(api_key="key")
        with patch.object(adapter, "_client", return_value=client):
            with pytest.raises(ModelError) as exc:
                await adapter.generate(task)
        assert exc.value.code == "budget_exceeded"
    asyncio.run(_test())


def test_runtime_handles_asyncio_cancellation():
    async def _test():
        client = MagicMock()
        client.aio.models.generate_content = AsyncMock(side_effect=asyncio.CancelledError())
        adapter = GeminiAdapter(api_key="key")
        with patch.object(adapter, "_client", return_value=client):
            with pytest.raises(ModelError) as exc:
                await adapter.generate(_task("cancel"))
        assert exc.value.code == "cancelled"
    asyncio.run(_test())


def test_telemetry_record_call_is_invoked():
    async def _test():
        reset_usage_summary()
        provider = FakeProvider(scripted=[ModelResult(text="{}", parsed={}, usage=TokenUsage(prompt=10, completion=5, total=15), provider="fake", model="m", latency_ms=1, finish_reason="stop")])
        await with_retry(provider, _task("call"))
        assert get_usage_summary()["calls"] == 1
    asyncio.run(_test())


def test_circuit_breaker_opens_on_consecutive_failures():
    async def _test():
        from risk_dashboard.platform.ai_runtime.retry import reset_circuit_breaker
        try:
            errs = [ModelError("provider_unavailable", "fail", retryable=True) for _ in range(5)]
            provider = FakeProvider(scripted=errs + [ModelResult(text="ok", provider="fake", model="m", latency_ms=1, finish_reason="stop")])
            task = _task("circuit")
            for _ in range(5):
                with pytest.raises(ModelError):
                    await with_retry(provider, task, max_retries=0)
            with pytest.raises(ModelError) as exc:
                await with_retry(provider, task, max_retries=0)
            assert exc.value.code == "provider_unavailable" and exc.value.retryable is False
        finally:
            reset_circuit_breaker()
    asyncio.run(_test())


def test_size_limit_rejects_oversized_prompt():
    async def _test():
        provider = FakeProvider(scripted=[ModelResult(text="ok", provider="fake", model="m", latency_ms=1, finish_reason="stop")])
        with pytest.raises(ModelError) as exc:
            await with_retry(provider, _task("A" * 100_001))
        assert exc.value.code == "configuration_error"
    asyncio.run(_test())


def test_pii_redaction_masks_email_and_phone():
    text = "Liên hệ user@test.com sđt 0912345678 cccd 001234567890"
    redacted = redact_text(text)
    assert "[REDACTED_PII]" in redacted and "user@test.com" not in redacted and "0912345678" not in redacted
    redacted_task = redact_for_provider(_task(text))
    assert "[REDACTED_PII]" in redacted_task.messages[0].content


def test_structured_output_repair_budget_loop():
    schema = {"type": "object", "properties": {"val": {"type": "number"}}, "required": ["val"]}
    repairs = 0
    def repair(bad, err):
        nonlocal repairs
        repairs += 1
        return '{"val": 42}'
    res = parse_structured('{"invalid": true}', schema=schema, repair_fn=repair, max_repairs=2)
    assert res == {"val": 42} and repairs == 1


def test_news_translator_uses_ai_runtime_provider():
    mock_prov = MagicMock(spec=LLMProvider)
    mock_prov.generate = AsyncMock(return_value=ModelResult(
        text='{"headline_vi": "Tiêu đề", "summary_vi": "Tóm tắt"}',
        parsed={"headline_vi": "Tiêu đề", "summary_vi": "Tóm tắt"},
        provider="mock", model="m", latency_ms=1, finish_reason="stop",
    ))
    translator = NewsTranslator(provider=mock_prov)
    assert hasattr(translator, "provider")
    with patch("requests.post") as mock_post, patch.object(translator, "_get_cached", return_value=None):
        res = translator.translate_item({"headline": "Title", "summary": "Sum"})
        mock_post.assert_not_called()
        assert mock_prov.generate.called and res["headline_vi"] == "Tiêu đề"


def test_pyproject_has_no_openai_dependencies():
    content = Path(__file__).resolve().parent.parent.joinpath("pyproject.toml").read_text(encoding="utf-8")
    assert "langchain-openai" not in content


def test_app_factory_loads_dotenv(monkeypatch: pytest.MonkeyPatch):
    import dotenv
    loaded = False
    def fake_load(*_, **__):
        nonlocal loaded
        loaded = True
        return True
    monkeypatch.setattr(dotenv, "load_dotenv", fake_load)
    if hasattr(app_factory_module, "load_dotenv"):
        monkeypatch.setattr(app_factory_module, "load_dotenv", fake_load)
    app_factory_module.create_app()
    assert loaded
