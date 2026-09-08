import asyncio
from dotenv import load_dotenv

load_dotenv()

from risk_dashboard.platform.ai_runtime.factory import get_provider
from risk_dashboard.platform.ai_runtime.contracts import ModelTask, ModelMessage

async def main():
    provider = get_provider()
    print(f"Provider: {provider.name}, Model: {provider.default_model}")

    # Health check
    healthy = await provider.health()
    print(f"Health: {'✅ OK' if healthy else '❌ FAIL'}")

    # Simple generation
    task = ModelTask(
        task_id="test_gen", task_type="test", system_instructions_ref="default", correlation_id="test",
        messages=(ModelMessage(role="user", content="Trả lời bằng 1 câu: VN-Index là gì?"),),
    )
    try:
        result = await provider.generate(task)
        print(f"Generate: {'✅ OK' if result.text else '❌ EMPTY'}")
        print(f"Response preview: {result.text[:200]}...")
    except Exception as e:
        print(f"Generate: ❌ FAIL - {e}")

    # Structured output (JSON mode)
    json_task = ModelTask(
        task_id="test_json", task_type="test", system_instructions_ref="default", correlation_id="test",
        messages=(ModelMessage(role="user",
            content='Trả về JSON nguyên bản, không dùng block ```json: {"market": "VN", "index_name": "VN-Index", "type": "benchmark"}'),),
        settings={"response_mime_type": "application/json"},
    )
    try:
        json_result = await provider.generate(json_task)
        print(f"Structured: {'✅ OK' if '{' in json_result.text else '❌ NOT JSON'}")
        print(f"JSON preview: {json_result.text[:200]}")
    except Exception as e:
        print(f"Structured: ❌ FAIL - {e}")

asyncio.run(main())
