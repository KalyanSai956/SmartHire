from __future__ import annotations

from collections.abc import Callable

from backend.services.job_sources.amazon import AmazonAdapter
from backend.services.job_sources.base import JobSourceAdapter

AdapterFactory = Callable[[], JobSourceAdapter]
_ADAPTERS: dict[str, AdapterFactory] = {}
_LOADED = False


def register_adapter(provider: str, factory: AdapterFactory) -> None:
    key = str(provider).strip().lower()
    if not key:
        raise ValueError("Provider name cannot be empty")
    _ADAPTERS[key] = factory


def load_source_adapters() -> None:
    global _LOADED
    if _LOADED:
        return
    register_adapter("amazon", AmazonAdapter)
    _LOADED = True


def get_adapter(provider: str) -> JobSourceAdapter:
    load_source_adapters()
    key = str(provider).strip().lower()
    factory = _ADAPTERS.get(key)
    if factory is None:
        raise ValueError(f"No job source adapter registered for provider={provider}")
    return factory()


def registered_providers() -> list[str]:
    load_source_adapters()
    return sorted(_ADAPTERS)
