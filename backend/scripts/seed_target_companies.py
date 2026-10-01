from __future__ import annotations

import asyncio

import httpx

from backend.core.config import (
    SUPABASE_KEY,
    SUPABASE_URL,
)

from backend.services.jobs.company_registry import (
    get_target_companies,
)


def headers() -> dict[str, str]:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": (
            "resolution=merge-duplicates,"
            "return=minimal"
        ),
    }


async def main() -> None:

    companies = get_target_companies()

    records = [
        {
            "name": company.name,
            "slug": company.slug,
            "category": company.category,
            "careers_url": company.careers_url,
            "website_url": company.website_url,
            "source_type": "career_portal",
            "is_target_company": True,
            "country": "India",
            "priority": company.priority,
        }
        for company in companies
    ]

    url = (
        f"{SUPABASE_URL.rstrip('/')}"
        "/rest/v1/companies"
    )

    async with httpx.AsyncClient(
        timeout=60
    ) as client:

        response = await client.post(
            url,
            headers=headers(),
            params={
                "on_conflict": "slug",
            },
            json=records,
        )

        response.raise_for_status()

    print(
        f"Seeded {len(records)} target companies."
    )


if __name__ == "__main__":
    asyncio.run(main())