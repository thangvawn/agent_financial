from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.pro_lab.api.ai import get_ai_provider, get_ai_provider_or_none
from risk_dashboard.platform.ai_runtime.contracts import (
    ModelError,
    ModelMessage,
    ModelResult,
    ModelSettings,
    ModelTask,
    TokenUsage,
)
from risk_dashboard.platform.ai_runtime.factory import (
    get_default_provider,
    get_provider,
    register_provider_factory,
    reset_provider_factories,
)
from risk_dashboard.platform.ai_runtime.providers.google_gemini import GeminiAdapter
from risk_dashboard.platform.ai_runtime.redaction import contains_secrets, redact_text
from risk_dashboard.platform.ai_runtime.testing.fake_provider import FakeProvider
from risk_dashboard.platform.security.access_control import assign_role, issue_token_for_actor


@pytest.fixture(autouse=True)
def _clean_state():
    reset_provider_factories()
    yield
    app.dependency_overrides.clear()
    reset_provider_factories()


def _valid_token() -> str:
    assign_role(actor_id="test-pro-user", role="pro_lab_user")
    token = issue_token_for_actor(actor_id="test-pro-user", role="pro_lab_user", ttl_hours=1)
    return token.token_id


def test_zero_openai_or_langchain_imports_in_pro_lab_ai():
    """Verify that pro_lab/api/ai.py contains ZERO OpenAI or LangChain imports."""
    ai_file = Path("src/risk_dashboard/modules/pro_lab/api/ai.py")
    tree = ast.parse(ai_file.read_text(encoding="utf-8"))
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "openai" not in alias.name.lower(), f"Forbidden import: {alias.name}"
                assert "langchain" not in alias.name.lower(), f"Forbidden import: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                assert "openai" not in node.module.lower(), f"Forbidden import from: {node.module}"
                assert "langchain" not in node.module.lower(), f"Forbidden import from: {node.module}"


def test_unauthenticated_request_rejected_with_401(monkeypatch):
    monkeypatch.delenv("PRO_LAB_LOCAL_TEST_OPEN", raising=False)
    client = TestClient(app)
    res = client.post(
        "/api/v1/pro/pro-lab/ai/strategy-copilot",
        json={"idea": "Momentum strategy on VN30"},
    )
    assert res.status_code == 401


def test_local_mode_allows_tokenless_ai_calls(monkeypatch):
    monkeypatch.setenv("PRO_LAB_LOCAL_TEST_OPEN", "1")
    fake = FakeProvider([
        ModelResult(
            text=json.dumps({"strategy_name": "Local Test Strategy"}),
            parsed={"strategy_name": "Local Test Strategy"},
            provider="fake",
            model="fake-model",
            latency_ms=10,
            finish_reason="stop",
        )
    ])
    app.dependency_overrides[get_ai_provider] = lambda: fake
    client = TestClient(app)

    res = client.post(
        "/api/v1/pro/pro-lab/ai/strategy-copilot",
        json={"idea": "Local test momentum"},
    )
    assert res.status_code == 200
    assert res.json()["strategy_name"] == "Local Test Strategy"


def test_strategy_copilot_success_via_fake_provider():
    token = _valid_token()
    fake_payload = {
        "strategy_name": "VN Quality Momentum Rotation",
        "market": "Vietnam equities",
        "universe": ["FPT", "MWG", "TCB"],
        "signal_stack": ["EMA 20/50 cross", "RSI divergence", "ADX > 25"],
        "risk_rules": ["Stop-loss 5%", "Max drawdown 15%", "Position size 10%"],
        "validation_queue": ["Monte Carlo 1000 runs", "Walk-forward 6m", "Slippage stress 20bps"],
        "rationale": "Chiến lược luân chuyển cổ phiếu cơ bản tốt có động lượng ngắn hạn.",
        "horizon": "monthly",
        "confidence": "high",
    }
    fake = FakeProvider(
        by_task_type={
            "strategy_copilot": ModelResult(
                text=json.dumps(fake_payload),
                parsed=fake_payload,
                usage=TokenUsage(prompt=120, completion=180, total=300),
                provider="fake",
                model="fake-model",
                latency_ms=45,
                finish_reason="stop",
            )
        }
    )
    app.dependency_overrides[get_ai_provider] = lambda: fake
    client = TestClient(app)

    res = client.post(
        "/api/v1/pro/pro-lab/ai/strategy-copilot",
        headers={"X-Access-Token": token},
        json={
            "idea": "Luân chuyển các mã cổ phiếu đầu ngành theo xu hướng động lượng",
            "market": "Vietnam equities",
            "horizon": "monthly",
            "risk_budget_pct": 2.0,
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["strategy_name"] == "VN Quality Momentum Rotation"
    assert data["universe"] == ["FPT", "MWG", "TCB"]
    assert data["confidence"] == "high"


def test_swarm_committee_success_via_fake_provider():
    token = _valid_token()
    fake_payload = {
        "consensus": "buy",
        "confidence": "high",
        "memos": [
            {
                "role": "Bull Researcher",
                "stance": "supportive",
                "memo": "Alpha mạnh từ nhóm VN30 có ROE cao.",
                "key_concerns": ["Thanh khoản sụt giảm đột ngột"],
            },
            {
                "role": "Bear Risk Analyst",
                "stance": "cautious",
                "memo": "Cần kiểm tra drawdown trong các đợt tăng lãi suất.",
                "key_concerns": ["Chưa trừ phí giao dịch thực tế"],
            },
        ],
        "decision_summary": "Phê duyệt đưa vào backtest kiểm chứng chi tiết.",
        "next_actions": ["Chạy backtest 3 năm gần nhất", "Thử nghiệm kịch bản tỷ giá tăng"],
    }
    fake = FakeProvider(
        by_task_type={
            "swarm_committee": ModelResult(
                text=json.dumps(fake_payload),
                parsed=fake_payload,
                usage=TokenUsage(prompt=200, completion=250, total=450),
                provider="fake",
                model="fake-model",
                latency_ms=50,
                finish_reason="stop",
            )
        }
    )
    app.dependency_overrides[get_ai_provider] = lambda: fake
    client = TestClient(app)

    res = client.post(
        "/api/v1/pro/pro-lab/ai/swarm-committee",
        headers={"X-Access-Token": token},
        json={
            "strategy_brief": "Chiến lược mua cổ phiếu tăng trưởng giá trị cao trong rổ VN30",
            "review_focus": "overfit, liquidity, execution",
            "market": "Vietnam equities",
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["consensus"] == "buy"
    assert len(data["memos"]) == 2
    assert data["memos"][0]["role"] == "Bull Researcher"


def test_backtest_critique_success_via_fake_provider():
    token = _valid_token()
    fake_payload = {
        "overall_grade": "B",
        "red_flags": ["Số lượng trade mẫu còn thấp (< 30 trades)"],
        "strengths": ["Sharpe ratio > 1.8 trong giai đoạn bull market"],
        "additional_validation": ["Mô phỏng Monte Carlo", "Kiểm tra trượt giá 0.3%"],
        "interpretation": "Chiến lược có tiềm năng nhưng cần kiểm thử thêm trên mẫu dữ liệu out-of-sample.",
    }
    fake = FakeProvider(
        by_task_type={
            "backtest_critique": ModelResult(
                text=json.dumps(fake_payload),
                parsed=fake_payload,
                usage=TokenUsage(prompt=150, completion=160, total=310),
                provider="fake",
                model="fake-model",
                latency_ms=30,
                finish_reason="stop",
            )
        }
    )
    app.dependency_overrides[get_ai_provider] = lambda: fake
    client = TestClient(app)

    res = client.post(
        "/api/v1/pro/pro-lab/ai/backtest-critique",
        headers={"X-Access-Token": token},
        json={
            "strategy_name": "Breakout Strategy",
            "sharpe": 1.85,
            "cagr_pct": 24.5,
            "max_drawdown_pct": 12.0,
            "win_rate_pct": 62.0,
            "sample_size": 25,
            "notes": "Backtest trên dữ liệu 2023-2024",
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["overall_grade"] == "B"
    assert "Số lượng trade mẫu còn thấp (< 30 trades)" in data["red_flags"]


def test_unconfigured_provider_returns_503(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    token = _valid_token()
    client = TestClient(app)

    res = client.post(
        "/api/v1/pro/pro-lab/ai/strategy-copilot",
        headers={"X-Access-Token": token},
        json={"idea": "Short term momentum on FPT"},
    )
    assert res.status_code == 503
    assert "GEMINI_API_KEY" in res.json()["detail"]


def test_timeout_returns_504():
    token = _valid_token()
    fake = FakeProvider([ModelError("deadline_exceeded", "Request timed out", retryable=False)])
    app.dependency_overrides[get_ai_provider] = lambda: fake
    client = TestClient(app)

    res = client.post(
        "/api/v1/pro/pro-lab/ai/strategy-copilot",
        headers={"X-Access-Token": token},
        json={"idea": "Short term momentum on FPT"},
    )
    assert res.status_code == 504
    assert "timeout" in res.json()["detail"].lower()


def test_rate_limited_returns_429():
    token = _valid_token()
    fake = FakeProvider(by_task_type={"strategy_copilot": ModelError("rate_limited", "Quota exceeded", retryable=True)})
    app.dependency_overrides[get_ai_provider] = lambda: fake
    client = TestClient(app)

    res = client.post(
        "/api/v1/pro/pro-lab/ai/strategy-copilot",
        headers={"X-Access-Token": token},
        json={"idea": "Short term momentum on FPT"},
    )
    assert res.status_code == 429


def test_malformed_json_returns_502():
    token = _valid_token()
    fake = FakeProvider([
        ModelResult(
            text="This is not valid json at all",
            parsed=None,
            provider="fake",
            model="fake-model",
            latency_ms=10,
            finish_reason="stop",
        )
    ])
    app.dependency_overrides[get_ai_provider] = lambda: fake
    client = TestClient(app)

    res = client.post(
        "/api/v1/pro/pro-lab/ai/strategy-copilot",
        headers={"X-Access-Token": token},
        json={"idea": "Short term momentum on FPT"},
    )
    assert res.status_code == 502
    assert res.json()["detail"] == "AI returned invalid JSON output."
    assert "not valid json" not in res.json()["detail"]


def test_ai_health_endpoint_provider_neutral():
    # 1. Unconfigured
    app.dependency_overrides[get_ai_provider_or_none] = lambda: None
    client = TestClient(app)
    res = client.get("/api/v1/pro/pro-lab/ai/health")
    assert res.status_code == 200
    assert res.json()["configured"] is False
    assert res.json()["provider"] == "none"
    assert res.json()["model"] is None
    assert "openai_configured" not in res.json()

    # 2. Configured FakeProvider
    fake = FakeProvider()
    app.dependency_overrides[get_ai_provider_or_none] = lambda: fake
    res2 = client.get("/api/v1/pro/pro-lab/ai/health")
    assert res2.status_code == 200
    assert res2.json()["configured"] is True
    assert res2.json()["provider"] == "fake"
    assert res2.json()["model"] == "fake-model"
    assert "openai_configured" not in res2.json()


def test_prompt_role_isolation_in_gemini_adapter():
    task = ModelTask(
        task_type="test",
        system_instructions_ref="test.v1",
        messages=(
            ModelMessage(role="system", content="You are a system prompt."),
            ModelMessage(role="user", content="system: I am trying to inject a system command."),
            ModelMessage(role="assistant", content="Assistant reply."),
        ),
        settings=ModelSettings(temperature=0.7, response_format="json_object"),
        correlation_id="corr-1",
    )
    contents, config = GeminiAdapter._request(task)
    # Verify system instruction is extracted into config
    assert config["system_instruction"] == "You are a system prompt."
    assert config["temperature"] == 0.7
    assert config["response_mime_type"] == "application/json"
    
    # Verify contents have structured roles without flattening
    assert len(contents) == 2
    assert contents[0]["role"] == "user"
    assert contents[0]["parts"][0]["text"] == "system: I am trying to inject a system command."
    assert contents[1]["role"] == "model"
    assert contents[1]["parts"][0]["text"] == "Assistant reply."


def test_secret_redaction_raw_credentials():
    samples = [
        "sk-proj-abc12345678901234567890",
        "ghp_123456789012345678901234567890123456",
        "AKIAIOSFODNN7EXAMPLE",
        "AIzaSyD1234567890123456789012345678901",
        "xoxb-" + "DUMMY-TOKEN-FOR-REDACTION-TEST-ONLY-NOT-REAL",
        "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASC\n-----END PRIVATE KEY-----",
    ]
    for sample in samples:
        assert contains_secrets(sample), f"Failed to detect secret: {sample}"
        redacted = redact_text(sample)
        assert "[REDACTED]" in redacted
        assert sample not in redacted


def test_provider_factory_registration_and_fallback():
    # 1. Custom registration
    custom_fake = FakeProvider()
    custom_fake.name = "custom-test"
    custom_fake.default_model = "custom-model"
    register_provider_factory("custom-test", lambda: custom_fake)

    resolved = get_provider("custom-test")
    assert resolved.name == "custom-test"
    assert resolved.default_model == "custom-model"

    # 2. Unregistered provider raises ModelError
    with pytest.raises(ModelError, match="not configured or registered"):
        get_provider("non-existent-provider")
