from __future__ import annotations

import asyncio

import httpx

from backend.core.config import SUPABASE_KEY, SUPABASE_URL
from backend.services.jobs.company_registry import get_target_companies
from backend.services.jobs.company_source_registry import (
    get_enabled_company_source_configs,
)


def _headers() -> dict[str, str]:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def _url(table: str) -> str:
    return f"{SUPABASE_URL.rstrip('/')}/rest/v1/{table}"


async def _disable_unused_sources(
    client: httpx.AsyncClient,
    active_providers: set[str],
) -> None:
    provider_list = ",".join(sorted(active_providers))

    response = await client.patch(
        _url("job_sources"),
        params={
            "provider": f"not.in.({provider_list})",
        },
        headers=_headers(),
        json={
            "enabled": False,
            "source_status": "disabled",
        },
    )
    response.raise_for_status()


async def sync_companies() -> dict[str, int]:
    companies = get_target_companies()

    company_records = [
        {
            "name": company.name,
            "slug": company.slug,
            "category": company.category,
            "website_url": company.website_url,
            "careers_url": company.careers_url,
            "logo_url": company.logo_url,
            "priority": company.priority,
            "is_target_company": True,
            "source_status": "registered",
            "country": "India",
        }
        for company in companies
    ]

    headers = {
        **_headers(),
        "Prefer": "resolution=merge-duplicates,return=representation",
    }

    enabled_configs = get_enabled_company_source_configs()

    active_providers = {
        (
            config.company_slug
            if config.provider == "career_portal"
            else config.provider
        ).strip().lower()
        for config in enabled_configs
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            _url("companies"),
            params={"on_conflict": "slug"},
            headers=headers,
            json=company_records,
        )
        response.raise_for_status()

        synced_companies = response.json()

        company_map = {
            row["slug"]: row["id"]
            for row in synced_companies
            if row.get("slug") and row.get("id")
        }

        await _disable_unused_sources(
            client,
            active_providers,
        )

        source_records = []

        for config in enabled_configs:
            company_id = company_map.get(config.company_slug)

            if not company_id:
                continue

            provider = config.provider

            if provider == "career_portal":
                provider = config.company_slug

            source_records.append(
                {
                    "company_id": company_id,
                    "provider": provider,
                    "board_token": config.board_token,
                    "enabled": True,
                    "source_url": config.source_url,
                    "api_url": config.api_url,
                    "provider_config": config.provider_config or {},
                    "source_status": "configured",
                    "error_count": 0,
                    "source_type": config.source_type,
                }
            )

        if source_records:
            source_response = await client.post(
                _url("job_sources"),
                params={"on_conflict": "company_id,provider"},
                headers=headers,
                json=source_records,
            )
            source_response.raise_for_status()

    return {
        "companies": len(company_records),
        "sources": len(source_records),
    }


if __name__ == "__main__":
    result = asyncio.run(sync_companies())
    print(result)