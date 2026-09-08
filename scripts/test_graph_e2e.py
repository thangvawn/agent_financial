import asyncio
from dotenv import load_dotenv

load_dotenv()

from risk_dashboard.modules.agentic_core.application.graph import run_graph
from risk_dashboard.platform.ai_runtime.factory import get_provider
from risk_dashboard.platform.ai_runtime.contracts import ModelTask, ModelMessage
from risk_dashboard.modules.agentic_core.schemas.envelope import TrustedExecutionEnvelope, ResourceRef, ExecutionBudget
from risk_dashboard.modules.auth.schemas.principal import ConsentSnapshot
from risk_dashboard.modules.agentic_core.infrastructure.quant_tool import QuantRiskReadOnlyTool

async def main():
    provider = get_provider()
    
    envelope = TrustedExecutionEnvelope(
        run_id="run_123", correlation_id="run_123", idempotency_key="run_123",
        account_id="test_acc", scopes=("agentic:run:execute",), surface="test",
        allowed_capabilities=("quant:read",),
        resource_refs=(), locale="vi-VN", policy_version="1.0.0", model_policy_version="1.0.0",
        consent=ConsentSnapshot(memory=True, analytics=True, consented_at="2026-01-01T00:00:00Z", policy_version="1.0"),
        created_at="2026-09-07T00:00:00Z",
        budget=ExecutionBudget(max_steps=5, max_tool_calls=2)
    )

    task = ModelTask(
        task_id="task_123", task_type="agentic", system_instructions_ref="default",
        correlation_id="run_123", messages=(ModelMessage(role="user", content="Phân tích rủi ro VaR của VN-Index"),),
    )

    print("Testing Happy Path...")
    result = await run_graph(envelope, task, provider, QuantRiskReadOnlyTool())
    print(f"Result Status: {result['status']}, Steps: {result['steps_used']}")

asyncio.run(main())
