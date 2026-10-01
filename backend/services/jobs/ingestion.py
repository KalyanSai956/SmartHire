from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from backend.database.supabase_db import (
    _get_headers,
    _get_rest_url,
    supabase_rest_get,
)

from backend.services.job_sources.registry import (
    load_source_adapters,
)
from backend.services.job_sources.router import (
    fetch_jobs_for_source,
)

from backend.services.jobs.company_registry import (
    get_target_companies,
)

from backend.services.jobs.job_cap import (
    enforce_active_job_cap,
)

from backend.services.jobs.job_classification_persistence import (
    classify_jobs,
)

from backend.services.jobs.job_indexer import (
    index_jobs,
)

from backend.services.jobs.location_normalizer import (
    normalize_location,
)

from backend.services.jobs.source_registry import (
    is_provider_allowed,
)


logger = logging.getLogger(
    __name__
)


def normalize_job_record(
    job,
) -> dict | None:
    location_result = normalize_location(
        raw_location=getattr(
            job,
            "location",
            None,
        ),
        remote_type=getattr(
            job,
            "remote_type",
            None,
        ),
    )

    if (
        not location_result.is_valid
        or not location_result.is_india
    ):
        logger.info(
            "Skipping non-India/invalid job: "
            "title=%s location=%s",
            getattr(
                job,
                "title",
                "Unknown",
            ),
            getattr(
                job,
                "location",
                None,
            ),
        )

        return None

    record = job.model_dump(
        mode="json"
    )

    record["location_country"] = (
        location_result.country
    )

    record["location_city"] = (
        location_result.city
    )

    record["location_region"] = (
        location_result.region
    )

    record["location_display"] = (
        location_result.display
    )

    record["location"] = (
        location_result.display
    )

    return record


async def classify_source_jobs(
    source_id: str,
) -> dict[str, int]:
    jobs = await supabase_rest_get(
        "jobs",
        {
            "source_id": (
                f"eq.{source_id}"
            ),
            "is_active": "eq.true",
            "location_country": "eq.India",
            "select": (
                "id,"
                "title,"
                "description,"
                "skills,"
                "experience_level,"
                "classification_version,"
                "classified_at,"
                "job_family"
            ),
        },
    )

    if not jobs:
        return {
            "classified": 0,
            "skipped": 0,
        }

    return await classify_jobs(
        jobs=jobs,
        force=False,
    )


async def sync_job_source(
    source: dict,
) -> dict:
    if not source.get(
        "enabled"
    ):
        raise ValueError(
            "Source is disabled"
        )

    load_source_adapters()

    jobs = await fetch_jobs_for_source(
        source
    )

    india_jobs = []
    rejected_jobs = 0

    for job in jobs:
        record = normalize_job_record(
            job
        )

        if record is None:
            rejected_jobs += 1
            continue

        india_jobs.append(
            record
        )

    logger.info(
        "Source %s fetched %s jobs: "
        "%s India jobs, %s rejected",
        source["provider"],
        len(jobs),
        len(india_jobs),
        rejected_jobs,
    )

    now = datetime.now(
        timezone.utc
    ).isoformat()

    records = [
        {
            **job,
            "last_seen_at": now,
            "is_active": True,
        }
        for job in india_jobs
    ]

    headers = {
        **_get_headers(),
        "Prefer": (
            "resolution=merge-duplicates,"
            "return=minimal"
        ),
    }

    if records:
        async with httpx.AsyncClient(
            timeout=60
        ) as client:
            for start in range(
                0,
                len(records),
                100,
            ):
                batch = records[
                    start:start + 100
                ]

                response = await client.post(
                    _get_rest_url(
                        "jobs"
                    ),
                    params={
                        "on_conflict": (
                            "provider,"
                            "source_job_id"
                        )
                    },
                    headers=headers,
                    json=batch,
                )

                response.raise_for_status()

    if len(jobs) > 0:
        async with httpx.AsyncClient(
            timeout=30
        ) as client:
            response = await client.patch(
                _get_rest_url(
                    "jobs"
                ),
                params={
                    "source_id": (
                        f"eq.{source['id']}"
                    ),
                    "last_seen_at": (
                        f"lt.{now}"
                    ),
                    "is_active": (
                        "eq.true"
                    ),
                },
                headers=_get_headers(),
                json={
                    "is_active": False
                },
            )

            response.raise_for_status()

    else:
        logger.warning(
            "Source %s returned 0 jobs. "
            "Skipping deactivation.",
            source["id"],
        )

    async with httpx.AsyncClient(
        timeout=30
    ) as client:
        response = await client.patch(
            _get_rest_url(
                "job_sources"
            ),
            params={
                "id": (
                    f"eq.{source['id']}"
                )
            },
            headers=_get_headers(),
            json={
                "last_synced_at": now,
                "last_error": None,
                "source_status": "healthy",
                "error_count": 0,
            },
        )

        response.raise_for_status()

    classification_result = (
        await classify_source_jobs(
            source_id=source["id"]
        )
    )

    logger.info(
        "Classification result for source=%s: "
        "classified=%s skipped=%s",
        source["id"],
        classification_result[
            "classified"
        ],
        classification_result[
            "skipped"
        ],
    )

    return {
        "source_id": source["id"],
        "provider": source["provider"],
        "fetched": len(jobs),
        "india_jobs": len(
            india_jobs
        ),
        "rejected": rejected_jobs,
        "classified": (
            classification_result[
                "classified"
            ]
        ),
        "classification_skipped": (
            classification_result[
                "skipped"
            ]
        ),
    }


async def mark_source_failed(
    source: dict,
    error: Exception,
) -> None:
    current_count = (
        source.get(
            "error_count"
        )
        or 0
    )

    error_message = str(
        error
    )

    async with httpx.AsyncClient(
        timeout=30
    ) as client:
        response = await client.patch(
            _get_rest_url(
                "job_sources"
            ),
            params={
                "id": (
                    f"eq.{source['id']}"
                )
            },
            headers=_get_headers(),
            json={
                "last_error": (
                    error_message[:2000]
                ),
                "source_status": "error",
                "error_count": (
                    current_count + 1
                ),
            },
        )

        response.raise_for_status()


async def sync_enabled_sources(
    *,
    embedder=None,
) -> list[dict]:
    load_source_adapters()

    sources = await supabase_rest_get(
        "job_sources",
        {
            "enabled": "eq.true",
            "select": "*",
        },
    )

    target_company_slugs = {
        company.slug
        for company in get_target_companies()
    }

    target_companies = (
        await supabase_rest_get(
            "companies",
            {
                "slug": (
                    "in.("
                    + ",".join(
                        target_company_slugs
                    )
                    + ")"
                ),
                "select": "id,slug",
            },
        )
    )

    target_company_ids = {
        str(company["id"])
        for company in target_companies
        if company.get("id")
    }

    sources = [
        source
        for source in sources
        if (
            str(
                source.get(
                    "company_id"
                )
                or ""
            )
            in target_company_ids
        )
        and is_provider_allowed(
            str(
                source.get(
                    "provider"
                )
                or ""
            )
        )
    ]

    results = []

    for source in sources:
        try:
            result = await sync_job_source(
                source=source
            )

            results.append(
                result
            )

        except Exception as exc:
            logger.exception(
                "Job source sync failed: %s",
                source["id"],
            )

            try:
                await mark_source_failed(
                    source,
                    exc,
                )
            except Exception:
                logger.exception(
                    "Failed to update "
                    "source error state: %s",
                    source["id"],
                )

            results.append(
                {
                    "source_id": source["id"],
                    "provider": source[
                        "provider"
                    ],
                    "error": (
                        "Sync failed; "
                        "see backend logs"
                    ),
                }
            )

    try:
        cap_result = (
            await enforce_active_job_cap()
        )

        logger.info(
            "Global active job cap result: %s",
            cap_result,
        )

    except Exception:
        logger.exception(
            "Global active job cap "
            "enforcement failed"
        )

    if embedder is not None:
        try:
            indexed_count = (
                await index_jobs(
                    embedder=embedder
                )
            )

            logger.info(
                "Job RAG indexing completed: %s",
                indexed_count,
            )

        except Exception:
            logger.exception(
                "Job embedding/indexing failed"
            )

    return results