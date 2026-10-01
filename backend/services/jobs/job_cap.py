from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from typing import Any

import httpx

from backend.core.config import SUPABASE_KEY, SUPABASE_URL


logger = logging.getLogger(
    "smarthire.job_cap"
)

MAX_ACTIVE_JOBS = 500
BATCH_SIZE = 100


def _headers() -> dict[str, str]:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def _url(table: str) -> str:
    return (
        f"{SUPABASE_URL.rstrip('/')}"
        f"/rest/v1/{table}"
    )


def _date_key(
    value: Any,
) -> datetime:
    if not value:
        return datetime.min

    if isinstance(value, datetime):
        return value

    try:
        return datetime.fromisoformat(
            str(value).replace(
                "Z",
                "+00:00",
            )
        ).replace(
            tzinfo=None
        )
    except (
        TypeError,
        ValueError,
    ):
        return datetime.min


async def _get_target_companies() -> list[dict[str, Any]]:
    async with httpx.AsyncClient(
        timeout=60.0
    ) as client:
        response = await client.get(
            _url("companies"),
            headers=_headers(),
            params={
                "select": (
                    "id,slug,name,priority"
                ),
                "is_target_company": "eq.true",
                "limit": "100",
            },
        )

        response.raise_for_status()

        rows = response.json()

    return (
        rows
        if isinstance(rows, list)
        else []
    )


async def _get_active_jobs() -> list[dict[str, Any]]:
    async with httpx.AsyncClient(
        timeout=60.0
    ) as client:
        response = await client.get(
            _url("jobs"),
            headers=_headers(),
            params={
                "select": (
                    "id,company_id,provider,"
                    "source_job_id,title,posted_at,"
                    "last_seen_at,first_seen_at"
                ),
                "is_active": "eq.true",
                "location_country": "eq.India",
                "limit": "5000",
            },
        )

        response.raise_for_status()

        rows = response.json()

    return (
        rows
        if isinstance(rows, list)
        else []
    )


def _timestamp(
    value: Any,
) -> float:
    date_value = _date_key(value)

    if date_value == datetime.min:
        return 0.0

    return (
        date_value - datetime(1970, 1, 1)
    ).total_seconds()


def _rank_job(
    job: dict[str, Any],
    company_priority: dict[str, int],
) -> tuple[
    int,
    float,
    float,
    float,
    str,
]:
    company_id = str(
        job.get("company_id") or ""
    )

    priority = company_priority.get(
        company_id,
        100,
    )

    return (
        priority,
        -_timestamp(
            job.get("posted_at")
        ),
        -_timestamp(
            job.get("last_seen_at")
        ),
        -_timestamp(
            job.get("first_seen_at")
        ),
        str(
            job.get("id") or ""
        ),
    )


def _select_balanced_jobs(
    jobs: list[dict[str, Any]],
    companies: list[dict[str, Any]],
) -> set[str]:
    company_priority = {
        str(company["id"]): int(
            company.get("priority") or 100
        )
        for company in companies
        if company.get("id")
    }

    grouped: dict[
        str,
        list[dict[str, Any]],
    ] = defaultdict(list)

    for job in jobs:
        company_id = str(
            job.get("company_id") or ""
        )

        if company_id in company_priority:
            grouped[company_id].append(
                job
            )

    for company_id in grouped:
        grouped[company_id].sort(
            key=lambda item: _rank_job(
                item,
                company_priority,
            )
        )

    ordered_company_ids = sorted(
        grouped,
        key=lambda company_id: (
            company_priority.get(
                company_id,
                100,
            ),
            company_id,
        ),
    )

    selected: set[str] = set()

    indexes = {
        company_id: 0
        for company_id in ordered_company_ids
    }

    while len(selected) < MAX_ACTIVE_JOBS:
        added = False

        for company_id in ordered_company_ids:
            index = indexes[company_id]
            company_jobs = grouped[
                company_id
            ]

            if index >= len(company_jobs):
                continue

            job_id = company_jobs[
                index
            ].get("id")

            if job_id:
                selected.add(
                    str(job_id)
                )

            indexes[company_id] = (
                index + 1
            )

            added = True

            if (
                len(selected)
                >= MAX_ACTIVE_JOBS
            ):
                break

        if not added:
            break

    return selected


async def enforce_active_job_cap() -> dict[str, int]:
    companies = await _get_target_companies()
    jobs = await _get_active_jobs()

    target_company_ids = {
        str(company["id"])
        for company in companies
        if company.get("id")
    }

    target_jobs = [
        job
        for job in jobs
        if str(
            job.get("company_id") or ""
        ) in target_company_ids
    ]

    selected_ids = _select_balanced_jobs(
        target_jobs,
        companies,
    )

    deactivate_ids = [
        str(job["id"])
        for job in jobs
        if str(
            job.get("id") or ""
        ) not in selected_ids
    ]

    if deactivate_ids:
        async with httpx.AsyncClient(
            timeout=60.0
        ) as client:
            for start in range(
                0,
                len(deactivate_ids),
                BATCH_SIZE,
            ):
                batch = deactivate_ids[
                    start:start + BATCH_SIZE
                ]

                response = await client.patch(
                    _url("jobs"),
                    headers=_headers(),
                    params={
                        "id": (
                            "in.("
                            + ",".join(batch)
                            + ")"
                        ),
                    },
                    json={
                        "is_active": False
                    },
                )

                response.raise_for_status()

    logger.info(
        "Active job cap enforced | "
        "before=%d | target=%d | "
        "selected=%d | deactivated=%d",
        len(jobs),
        len(target_jobs),
        len(selected_ids),
        len(deactivate_ids),
    )

    return {
        "before": len(jobs),
        "target_jobs": len(target_jobs),
        "active_jobs": len(selected_ids),
        "deactivated": len(
            deactivate_ids
        ),
    }