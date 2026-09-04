from __future__ import annotations

from risk_dashboard.platform.ai_runtime.provider import LLMProvider


async def check_provider_health(provider: LLMProvider) -> dict[str, bool | str]:
    return {"provider": provider.name, "healthy": await provider.health()}
