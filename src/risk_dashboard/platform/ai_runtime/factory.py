"""Provider-neutral factory and registry for AI Runtime LLM providers."""
from __future__ import annotations

from collections.abc import Callable

from risk_dashboard.platform.ai_runtime.contracts import ModelError
from risk_dashboard.platform.ai_runtime.provider import LLMProvider

_PROVIDER_FACTORIES: dict[str, Callable[[], LLMProvider]] = {}
_DEFAULT_PROVIDER_NAME: str = "gemini"


def register_provider_factory(name: str, factory: Callable[[], LLMProvider]) -> None:
    """Register a factory for a given provider name."""
    _PROVIDER_FACTORIES[name.lower()] = factory


def set_default_provider_name(name: str) -> None:
    """Set the default provider name."""
    global _DEFAULT_PROVIDER_NAME
    _DEFAULT_PROVIDER_NAME = name.lower()


def get_provider(name: str | None = None) -> LLMProvider:
    """Resolve an LLMProvider instance by name (or default)."""
    provider_name = (name or _DEFAULT_PROVIDER_NAME).lower()
    factory = _PROVIDER_FACTORIES.get(provider_name)
    if factory is not None:
        return factory()

    # Built-in fallback resolver for default providers
    if provider_name == "gemini":
        from risk_dashboard.platform.ai_runtime.providers.google_gemini import create_gemini_provider

        return create_gemini_provider()

    raise ModelError("configuration_error", f"AI provider '{provider_name}' is not configured or registered.")


def get_default_provider() -> LLMProvider:
    """Get the active default LLMProvider instance."""
    return get_provider(_DEFAULT_PROVIDER_NAME)


def reset_provider_factories() -> None:
    """Reset the factory registry to default state (for tests)."""
    global _DEFAULT_PROVIDER_NAME
    _PROVIDER_FACTORIES.clear()
    _DEFAULT_PROVIDER_NAME = "gemini"

