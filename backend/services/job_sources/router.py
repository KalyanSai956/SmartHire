from __future__ import annotations

from typing import Any

from backend.services.job_sources.registry import get_adapter, load_source_adapters, register_adapter, registered_providers


def _read_source_value(source: Any, name: str) -> Any:
    if isinstance(source, dict):
        return source.get(name)
    return getattr(source, name, None)


async def fetch_jobs_for_source(source: Any):
    load_source_adapters()
    provider = str(_read_source_value(source, "provider") or "").strip().lower()
    if not provider:
        raise ValueError("Missing job source provider")
    company_id = _read_source_value(source, "company_id")
    source_id = _read_source_value(source, "id") or _read_source_value(source, "source_id")
    if not company_id:
        raise ValueError("Missing job source company_id")
    if not source_id:
        raise ValueError("Missing job source id")
    if isinstance(source, dict):
        config = dict(source)
    elif hasattr(source, "model_dump"):
        config = source.model_dump(mode="json")
    elif hasattr(source, "__dict__"):
        config = dict(source.__dict__)
    else:
        config = {}
    adapter = get_adapter(provider)
    return await adapter.fetch_jobs(company_id=str(company_id), source_id=str(source_id), config=config)


__all__ = ["fetch_jobs_for_source", "get_adapter", "load_source_adapters", "register_adapter", "registered_providers"]
